# NEST architecture 仕様書 (LTM-1 v1.2)

**Architecture name**: **NEST** — **N**ode-bound **E**xecution **S**ession **T**ree (2026-04-27 命名)

---

**document type**: 運用 rule 仕様書 (NEST architecture の権威ソース)
**version**: LTM-1 v1.2 (semver: PATCH bump; v1.2 = manifest §2 GEN-region 注記 §5.2, 2026-07-02, Rs 承認 D3)
**scope**: THREAD project 全 task (本 rule 採用以降の新 task は完全準拠、既存 active task は次 milestone から段階適用)
**issued**: 2026-04-27
**author**: Claude (rs 承認確定論点 1-7 ベースで起草、5-CC Pre-Debate 経由で v1→v1.1 patch、2026-04-27 NEST 命名統合)
**precedent**:
- SSOT Integrity-43STEP COMPLETE (2026-04-20)、本 task 教訓を反映
- 並行 CC 上書き事象 (2026-04-20 16:43)、引き継ぎ事象を実例として参照
- rs 承認 2026-04-27: Claude 推奨ベース論点 1-7 全件確定
- 5-CC Pre-Debate (2026-04-27): 45 challenge ACCEPTED 大半、CRITICAL 5 件を v1.1 で fix、22 P-item を v3 defer
- 2026-04-27 命名: NEST / CASCADE-LT / GROVE の 3 候補から NEST 採択 (memory: `project_nest_architecture.md`)

---

## §0a v1.1 CHANGELOG (v1 → v1.1 fixes)

本 v1.1 は v1 の 5-CC Pre-Debate (2026-04-27) で発見された CRITICAL 5 件 + minor 2 件 + cross-ref 1 件のみ反映。残 22 P-item は v3 defer (post-deployment empirical evidence で個別 motivate されてから採用)。

| Fix | v1 §  | 概要 | Source |
|---|---|---|---|
| F1 | §3.5 | 親 COMPLETE auto-absorb row 削除 (§3.3 #6 と矛盾、false COMPLETE risk) | CC2 CHALLENGE-1 |
| F2 | §3.7 | DISCARDED→IN_PROGRESS 遷移削除、Soft-recovery は新 node 作成 (新 node_id) | CC2 CHALLENGE-2 |
| F3 | §4.2 | hash_pin field 削除、sidecar `.sha256` file pattern 採用 (vault は独立 .git なし、self-referential 不能) | CC3 CHALLENGE-1 |
| F4 | §5.2 | 「git advisory lock」削除 (`git lock-ref` 不存在)、3-tier hybrid (per-session signal + parent-mediated queue + flock(2)) | CC4 CHALLENGE-1 |
| F5 | §7.1 | root_goal TBD → 既存 rs-confirmed L0 採用 (`project_strategic_task_master_list_v2_2026-04-27.md:13` cite) | CC5 CHALLENGE-1 |
| F6 | §3.4 | 完了不能の rs ABORT/HALT 拡張は v3 defer、本 v1.1 は CLAUDE.md §運用20 + prohibited.md「プロセスkill承認必須」を§3.4 に明示 cross-ref | CC5 CHALLENGE-3 |
| F7 | §10 | SSOT cross-ref 追加: ctx_thresholds.sh / feedback_subsession_notifyback_protocol.md / Vault Write Permissions.md (重複記述回避) | NHA KA-3, KA-4, KA-8 STRONG ACCEPT |
| m1 | §4.3 | option I (rs direct) / II (CC self-detect) / III (Claude detect) の採番修正 (v1 は I 抜け) | minor (P-8 partial) |
| m2 | 全 | timestamp 全例を ISO 8601 +09:00 に正規化 (v1 は date-only / Z / 混在) | minor (P-23) |
| n1 | 全 | 本 architecture を **NEST (Node-bound Execution Session Tree)** と正式命名、title / §0 / §10 に反映 | 2026-04-27 命名 (Rs 採択) |

**v3 defer 一覧**: Appendix A 参照 (22 P-items)

---

## §0 本 rule の位置付け

本 rule は **NEST architecture** (Node-bound Execution Session Tree) の権威仕様書。NEST は THREAD プロジェクトの全作業を **「最終目標を頂点としたロジックツリー」** で管理し、各 node を **CC session 単位** で実行する architecture。本 rule は node lifecycle / session 引き継ぎ / 完了判定 / 失敗時 rollback / 並行運用の protocol を規定する。

**用語使い分け:**
- **NEST**: architecture 自体の名称 (chat / vault / memo で reference 用)
- **LTM-1**: 本 rule 文書の identifier (versioned: v1, v1.1, v2 等)
- 例: 「NEST に従い handoff を ...」「LTM-1 v1.1 §3.5 cascade rule」

本 rule は CLAUDE.md / userMemories / 各 task DEFINE と協調動作し、抵触時は CLAUDE.md > 本 rule > task DEFINE の順で優先。本 rule 自身の発効は CLAUDE.md への cross-ref 追加 (L3 cascade 経由) を前提とする。

---

## §1 用語定義

| 用語 | 定義 |
|---|---|
| **node** | ロジックツリー上の単位、1 つの「目標 + 手段」を持つ |
| **root node** | ロジックツリー頂点、project 全体の最終目標に対応 |
| **parent node** | 上位 node、子 node の集合で目標達成を実現 |
| **child node** | 下位 node、親 node の手段の一つ |
| **leaf node** | 子を持たない node、具体的 action を実行 |
| **session** | CC 1 instance による作業期間、1 conversation で完結 |
| **node ID** | node の永続識別子、tree 構造を反映 (例: `T-08-1-3`) |
| **session ID** | node に対する session 連番 (例: `T-08-1-3#s2`) |
| **handoff** | session 間で node 作業を引き継ぐ protocol |
| **goal** | node の目標 (1 文記述可能、検証可能条件付き) |
| **means** | node の手段 (子 node 群 or leaf 内 action) |
| **dependency** | node 間の依存関係 (precedent / blocker の 2 種類のみ。spawn / parallel は §2.1 注で別扱い) |

---

## §2 node の構造

### §2.1 node の必須要素

各 node は以下を持つ:

1. **node ID** (永続、tree 構造反映)
2. **goal** (1 文 + 検証可能条件)
3. **means** (子 node list or leaf 内 action description)
4. **status** (PENDING / IN_PROGRESS / HOLD / COMPLETE / ARCHIVED / DISCARDED)
5. **parent_node** (root node は null)
6. **children_nodes** (leaf node は空 list)
7. **dependencies** (precedent / blocker の 2 種類のみ — `precedent`: 完了必須、§3.1 #2 で消費 / `blocker`: 並行制約、§3.5 cascade で消費)
8. **session history** (本 node に対する session ID list、引き継ぎ chain)

**注 (v1.1):** v1 で `parallel` / `spawn` を dependency に含めていたが、`parallel` は §5.1 default で表現可、`spawn` は trace 関係 (`session_history` または別 `provenance:` field で表現) のため、dependency 4-edge taxonomy は YAGNI として 2-edge に縮小。

### §2.2 vault 配置

各 node は vault folder として実体化:

```
thread-vault/
├── 00-Project-Management/
│   ├── project-tree-manifest.md     ← project 全 node の親子関係 manifest
│   ├── operational-rule-LTM-1.md   ← 本 rule
│   └── _handoff/                    ← 引き継ぎ artifact 専用 folder
│       ├── node-T-08-1-3-handoff-s1.md
│       ├── node-T-08-1-3-handoff-s1.md.sha256   ← v1.1: sidecar hash file
│       ├── node-T-08-1-3-pins-s1.sha256          ← v1.1: 依存 file pin hashes
│       └── node-T-08-1-3-handoff-s2.md
├── T-08-DA-MPPI/                    ← root node 下の child (= 旧 08-DA-MPPI/)
│   ├── state.md                     ← node 識別 + status + metadata
│   ├── DEFINE-*.md
│   ├── T-08-1-Stage-A/              ← grand-child node
│   │   ├── state.md
│   │   └── ...
│   └── ...
├── T-09-RobotTAS-v1/
└── _archive/                        ← COMPLETE / ARCHIVED / DISCARDED node 移管先
```

### §2.3 state.md の必須 front matter

各 node の `state.md` 冒頭:

```yaml
---
node_id: T-08-1-3
node_name: DA-MPPI Stage A IK Convention Verification
goal: dry_run と wet_run の IK convention divergence を 0 件まで解消
goal_verification: 両 IK output の cos(π/8), sin(π/8) quat exact 一致
status: IN_PROGRESS  # PENDING / IN_PROGRESS / HOLD / COMPLETE / ARCHIVED / DISCARDED
parent_node: T-08-1
children_nodes: []  # leaf node なら空、内部 node なら ["T-08-1-3-1", "T-08-1-3-2"]
dependencies:
  precedent: ["T-08-1-2"]    # 完了必須
  blocker: []                 # 並行制約
session_history:
  - id: T-08-1-3#s1
    status: handed_off
    handoff_artifact: _handoff/node-T-08-1-3-handoff-s1.md
  - id: T-08-1-3#s2
    status: active
created: 2026-04-27T00:00:00+09:00      # v1.1: ISO 8601 +09:00
last_updated: 2026-04-27T15:30:00+09:00 # v1.1: ISO 8601 +09:00
---
```

---

## §3 lifecycle protocol

### §3.1 node 起動 (PENDING → IN_PROGRESS)

**起動条件**:
1. 親 node の `children_nodes` に登録済 (root node は project-tree-manifest.md に登録)
2. precedent dependency 全件 COMPLETE
3. goal が 1 文 + 検証可能条件で記述済
4. rs 承認 (起動承認、子 node 作成承認とは別 gate)

**起動手順**:
1. Claude が起動指示 draft 起草 (goal / means / dependencies 明示)
2. rs 承認 → vault folder 作成 + state.md 配置
3. CC session 1 起動、session ID = `{node_id}#s1`
4. session 冒頭: state.md preflight check (sidecar hash verify 含む、§4.4 参照)
5. status を IN_PROGRESS に更新

### §3.2 node 進行中の操作

session 中に発生する操作:

- **子 node spawn**: 必要に応じ子 node を新規作成、本 rule §3.1 起動 protocol を再帰適用
- **dependencies 更新**: precedent / blocker list の事後追加
- **handoff trigger**: §4 引き継ぎ protocol 適用条件発生時
- **means abandonment without goal abandonment** (v1.1 追記): 現 means が infeasible だが goal は achievable な場合、node は IN_PROGRESS 維持、現 means を session_history に superseded 記録、新 means を新子 node として spawn (DISCARDED 経由しない)

### §3.3 node 完了 (IN_PROGRESS → COMPLETE)

**完了条件**:
1. goal_verification の検証可能条件満たす
2. CC session が成果物生成 + 完了申告
3. Claude Layer 2 review PASS
4. rs 承認

**完了手順**:
1. CC が完了申告 (vault 内 closure log 生成、本 task の Phase 4c 慣習踏襲)
2. Claude Layer 2 review (rule #4 / #6 / #7 適用)
3. rs 承認
4. status を COMPLETE に更新
5. 親 node の `children_nodes` 内で本 node 完了 mark
6. **本 node が leaf でない場合: 全子 node が COMPLETE / ARCHIVED / DISCARDED であること verify (子未完了は親完了不可、§3.5 cascade 整合)**
7. handoff chain 記録: 全 session の summary を closure log に統合

### §3.4 node 完了不能判定 (IN_PROGRESS → DISCARDED)

**完了不能宣言可能主体**:

- **CC self-declare**: session 中に goal 達成不可能と判明、rs 通知 + Claude Layer 2 review
- **Claude detect**: Layer 2 review で goal 達成不能を発見、rs 通知
- **rs direct**: rs が直接判断 (scope 変更 / 方針転換)

**完了不能宣言の根拠要件**:
1. goal 達成不能の事実 base 根拠 (試行履歴 / 実測 / fact-inquiry)
2. 代替手段検討の有無 (3 案以上検討で全件不能 + 各案 infeasibility 証拠 attach、または明確な技術的 / scope 的 blocker)
3. 影響範囲評価 (親 node 目標への影響、兄弟 node への影響)

**プロセス kill / 強制停止に関する注意 (v1.1):** 完了不能判定の結果として CC が訓練プロセス・ハーネス・他 session 子プロセスを kill する場合は、CLAUDE.md §運用 20 + `.claude/rules/prohibited.md`「プロセスkill承認必須」+ `feedback_autonomous_kill_authorized.md` の permission cascade に従う。本 rule §3.4 から独立した stop 権限を付与しない。本 v1.1 では rs ABORT / HALT の signal-level extension は v3 defer。

**破棄処理 (option β 採用、成果物保全)**:
1. node folder を `_archive/discarded/{node_id}-{timestamp}/` に移管
2. 成果物は削除せず保全 (将来の参照可能性確保)
3. 親 node の `children_nodes` から本 node 除去
4. 親 node 目標再評価:
   - 親 node 目標が達成可能なら、新 means 起草 (新子 node) で続行
   - 親 node 目標が達成不能と判明なら、親 node も完了不能判定 (再帰的 cascade)
5. 兄弟 node + tree-global 依存 node への影響評価:
   - dependencies 上で本破棄 node を precedent / blocker としていた node (sibling + cross-tree) は HOLD 移行 + rs 通知
   - 「代替 precedent 設定」は rs 明示承認後に実施
   - manifest §5 archive list に最終 status snapshot を保持 (依存解決用)

**注 (v1.1):** DISCARDED node から復活させたい場合は、新 node_id (例: T-08-1-3-v2) で新 node 作成し、DISCARDED 先祖を `provenance:` field で参照する。DISCARDED → IN_PROGRESS の状態 mutation は禁止 (archive-move + parent-children-removal の整合性が崩れる)。

### §3.5 node 削除時の cascade rule (v1.1: 親 COMPLETE 自動吸収削除)

| 親 node 状態 | 子 node の扱い |
|---|---|
| **親 COMPLETE 申告時** | §3.3 #6 enforce: 全子が COMPLETE / ARCHIVED / DISCARDED でなければ親完了不可。未完了子があれば親完了申告 reject。**自動吸収 rule なし** (v1 の option γ 削除、false COMPLETE risk 排除) |
| **親 DISCARDED** | option β: 子は成果物保全のまま `_archive/orphan/` 移管、関係解除のみ |
| **親 ARCHIVED** | 子も親 archive folder 内に同梱、構造保全 |

**注**: 子 node が独立価値を持つ場合 (再利用可能な成果物 / 別系列で参照) は rs 判断で `_archive/discarded/` ではなく `_archive/legacy/` 等に分類可

### §3.6 node HOLD (一時停止)

**HOLD 条件**: rs 判断で一時停止 (HOLD は IN_PROGRESS の sub-state、session_history 必須)
**HOLD 中の挙動**: session 終了状態、再開時は新 session ID で起動 (引き継ぎ protocol §4 適用)
**HOLD 解除条件**: rs 明示判断
**注 (v1.1)**: PENDING からの直接 HOLD 遷移は不可 (session_history 空のため「再開」semantics 未定義)。起動前 defer は PENDING のままで rs 承認 hold 状態を表現。

### §3.7 node 状態遷移 図 (text、v1.1 修正)

```
PENDING → IN_PROGRESS
              ↓  ↑ (HOLD 解除で IN_PROGRESS 復帰)
              HOLD
              ↓
              DISCARDED → ARCHIVED (discarded archive)
              ↓
            COMPLETE → ARCHIVED (terminal、不可逆)
```

**Invalid transitions (明示):**
- DISCARDED → IN_PROGRESS: 禁止 (archive-move 整合性)。代わりに新 node_id で新 node 作成 + provenance reference
- HOLD → PENDING: 禁止 (session_history 抹消による audit loss)
- ARCHIVED → 任意: 禁止 (terminal)
- COMPLETE → IN_PROGRESS: 禁止 (再開は新 node)

---

## §4 session 引き継ぎ protocol

### §4.1 引き継ぎ pattern

**pattern α: 計画的引き継ぎ** (session A 完了 → session B 起動)
- session A が node を進行、context window / 担当領域変更で session 分割
- session A は handoff artifact 生成して終了 (node は IN_PROGRESS 維持)
- session B は handoff artifact から起動

**pattern β: 非計画的引き継ぎ** (session A 中断 → session B 継続)
- session A が context 限界 / クラッシュ / 中断
- session B が同 node を継続
- handoff artifact = session A の最終状態 snapshot (CC が emergency 生成 or rs/Claude が再構築)

**pattern γ: 並行委譲** (session A 進行中 + session B 部分担当)
- session A が親 node 進行、子 node を session B に委譲
- handoff artifact = 子 node の goal / scope / 親への報告 protocol (delegation contract、§4.2 別 template)

**pattern δ: 横断引き継ぎ** (session A から別系列 session C へ完全 transfer)
- 担当切替、session A 終了 + session C 完全引き継ぎ
- handoff artifact = full state snapshot + 認知 context

### §4.2 handoff artifact format (v1.1: sidecar hash protocol 採用)

**file 配置**: `thread-vault/00-Project-Management/_handoff/node-{node_id}-handoff-s{seq}.md`

**Hash protocol (v1.1, sidecar pattern):**

vault は独立 git repo ではない (`ls thread-vault/.git` → 不在) ため、git commit hash fallback 不可。self-referential hash は circular dependency のため、外部 sidecar file 方式を採用:

1. handoff artifact 本体 (`node-{id}-handoff-s{n}.md`) に hash field を含めない
2. sibling sidecar file `node-{id}-handoff-s{n}.md.sha256` を作成 (GNU coreutils format: `<sha256>  <basename>`)
3. 依存 file の pin hash は `node-{id}-pins-s{n}.sha256` に集約 (1 行 1 file、`sha256sum -c` 互換)
4. session B 検証時は `sha256sum -c node-{id}-handoff-s{n}.md.sha256` および pins file を実行

**必須 section** (snapshot 用 α/β/δ template):

```yaml
---
node_id: T-08-1-3
session_from: T-08-1-3#s1
session_to: T-08-1-3#s2
handoff_pattern: alpha / beta / delta
handoff_format_version: v1.1
created: 2026-04-27T15:30:00+09:00      # v1.1: ISO 8601 +09:00
session_seq: 2                           # total ordering 補助
---

## §1 node 現状 snapshot
- goal: ...
- 進捗 status: 完了済 step list / 残 step list
- 直近実施 action: ...

## §2 hash pin (依存 file 整合性、sidecar `.sha256` で検証)
| file | role |
|---|---|
| state.md | node metadata |
| DEFINE-*.md | node spec |
| 直近 3 modified artifact | 進捗成果物 |

## §3 判断履歴 (引き継ぎ前までの rs 判断 + 適用 option)
- 2026-04-27T10:00:00+09:00: rs 承認 ... → option ... 採用

## §4 active rule (本 node に適用される rule)
- self-imposed rule: ...
- scope 制約: ...
- 禁止事項: ...

## §5 残課題 + 次 session 着手事項
- 優先度 1: ...
- 優先度 2: ...

## §6 引き継ぎ理由 (pattern 別)
- α: 計画的、session A は ... で完了
- β: 中断、原因 ...
- δ: 横断、担当切替 ...

## §7 次 session 冒頭 preflight 必須項目
1. sidecar `.sha256` で本 file hash 一致確認
2. pins `.sha256` で全依存 file 照合
3. §4 active rule 認識確認
4. 不整合検出時 BLOCKED_FOR_USER + rs 通知
```

**γ pattern (delegation contract template、§4.2.1):**

pattern γ は snapshot ではなく contract のため別 template:

```yaml
---
node_id: T-08-1-3-1   # 委譲先子 node
parent_node: T-08-1-3
delegation_from: T-08-1-3#s2  # 親 session
delegation_to: T-08-1-3-1#s1  # 子 session
contract_format_version: v1.1
created: 2026-04-27T15:30:00+09:00
---

## §1 委譲 scope
- 子 node goal: ...
- scope_boundary: ...

## §2 親への報告 protocol
- 報告頻度: ...
- 完了通知 channel: ...

## §3 衝突解決 owner
- 子↔親 metadata conflict 時の責任主体: parent_session

## §4 hash pin (依存 file)
- (sidecar `.sha256` で検証)
```

### §4.3 引き継ぎ判定主体 (v1.1: option I/II/III 採番修正)

- **option I (rs direct)**: rs が直接判断、CC に handoff 指示
- **option II (CC self-detect)**: CC session 内で context window 残量低下 / 担当領域逸脱 / 複雑度急増 を検知して引き継ぎ提案を rs に通知
- **option III (Claude detect)**: Claude が rs/CC やりとりから引き継ぎ必要性を検知して rs 提案

**rs 最終承認**: option I/II/III いずれの提案でも rs 明示承認後に引き継ぎ実行

**Context window threshold (v1.1):** 本 rule は context % 値を再記述しない。`~/.claude/hooks/lib/ctx_thresholds.sh` を SSOT として参照 (FLAG_WRITE / SOFT / HARD / STALE_SECONDS の権威ソース、現値は変動可、ファイル参照で取得)。

### §4.4 引き継ぎ verify protocol (v1.1: 二段階 sidecar 検証)

**引き継ぎ先 session 冒頭で必須**:

1. handoff artifact の sidecar `.sha256` で本 file hash 確認
2. pins `.sha256` で全依存 file 照合 (sampling 不可、§5.2 整合)
3. node state.md の status 確認 (IN_PROGRESS であること、HANDED_OFF transient 状態でないこと)
4. §4 active rule の rs 認識確認

**不整合検出時**: 即 BLOCKED_FOR_USER + rs 緊急通知、引き継ぎ先 session は作業着手禁止。「軽微」分類による続行 path を提供しない (canonicalize で trivial diff は事前吸収する設計)。

**Canonicalize step (v1.1):** sidecar hash 計算前に file は canonicalize される (trailing whitespace strip / EOL normalize) ため、改行差や末尾 whitespace の trivial 差分は hash mismatch を引き起こさない。意味のある diff のみ mismatch を発生させる。

### §4.5 引き継ぎ失敗時の対応

| 失敗 pattern | 対応 |
|---|---|
| handoff hash mismatch | BLOCKED_FOR_USER、引き継ぎ元 session 状態調査 (rs/Claude 担当、artifact 再構築 owner は rs 明示判断) |
| handoff artifact 不在 | 引き継ぎ起動 invalid、rs 通知、必要なら artifact 再構築 (Claude default、CC fallback) |
| 引き継ぎ先 session 完了不能 | node 完了不能判定 (§3.4)、新 means 起草 |
| 引き継ぎ chain 過長 | empirical 閾値 (12h+ 累積 wall-clock OR 3+ pattern-β handoffs) で WARN、`feedback_cc1_session_close_discipline.md` 参照。閾値超過時は rs 判断で延長 / 新 node split |

---

## §5 並行運用 protocol

### §5.1 並行 CC session の許容

複数 CC session が project 内で同時稼働する場合:

- **異なる node に対する session**: 並行可、ただし共通 mutable file は §5.2 protocol で保護
- **同一 node の異なる session**: 引き継ぎ protocol 適用 (§4)、同時並行は禁止
- **親子関係 node の並行**: 親 node session が親自体の作業中 + 子 node が独立 session = 許容 (子は親に対し subset、§5.2 lock hierarchy 適用)

**Transition overlap protocol (v1.1):** session A → session B 引き継ぎ期間に session_state を導入:
- session_state ∈ {starting, running, draining, exited}
- node status 遷移は session A.session_state == exited を条件とする
- session B の preflight (§5.3) は session A.session_state == exited を確認後に進む

### §5.2 artifact 干渉防止 (v1.1: 3-tier hybrid lock)

並行 CC が同一 file への書き込み衝突を回避する 3-tier hybrid:

**Tier 1 — per-session signal files (既存 pattern 継続採用)**:
- per-session memory files: `~/.claude/projects/.../memory/handoff_cc_<task>_<phase>_<date>.md` (47 file empirical 確認、`feedback_subsession_notifyback_protocol.md` SSOT)
- per-node-per-session vault handoffs: `_handoff/node-<id>-handoff-s<seq>.md` (§4.2、session_id が filename に含まれる single-writer 保証)
- 単一 writer per file、lock 不要、mtime-based reconciliation

**Tier 2 — parent-mediated single-writer queue (vault 共通 file)**:
- vault 共通 file (`project-tree-manifest.md`、親 node の `state.md.children_nodes` 等) への write は `_edit_requests/<seq>-<child_node>.md` に deposit
- parent (CC#1 coordinator for manifest、親 session for parent state.md) が FIFO + priority drain
- atomic write: tempfile + `mv` (同一 filesystem) で torn write 防止
- priority levels: `anti_pattern_report > status_update > info`

**Tier 3 — flock(2) for short-hold compound operations**:
- `${XDG_RUNTIME_DIR}/claude-code/locks/<resource>.lock` (vault 外、persistence 不要)
- 30 秒以内の atomic compound operation 用 (例: 親 children_nodes に child を register する read-modify-write)
- OS-enforced、process death で auto-release

**禁止 (v1.1):** v1 の「git advisory lock」は git に該当 API 不存在 (`git lock-ref` は valid な git command ではない)、かつ vault は独立 git repo でない (parent IsaacLab repo 内 untracked)。git advisory lock 方式は採用しない。

**v1.2 注記 (2026-07-02, manifest §2 GEN 領域 — planning-surface consolidation, node T-ROOT-Planning-Surfaces-Consolidation-20260702, Rs 承認 D3):**

> 【v1.2 注記 — manifest §2 GEN 領域】manifest §2 は `build_nest_snapshot.py` の生成領域 (GEN marker) とする。node state.md の更新 = 本条の deposit、同一ターンの再生成 = drain とみなす (executor = state.md を更新した session; tempfile+mv [§5.3] + Tier 3 flock 必須)。§2 GEN 領域への手書きおよび manifest への UPDATE block 追記は禁止 (追記型 node 記録は state.md へ)。§1/§3/§4/§5 および `_edit_requests/` queue の運用は従前どおり (Tier 2 は非生成部向けに存続)。本注記は P17「direct write 永久禁止」の部分改定である。

### §5.3 preflight check (v1.1: parallelize + atomic write 強制)

session 冒頭 preflight に以下追加:

1. 自 node folder の hash 確認 (sidecar `.sha256` で照合、parallelize via `xargs -P 4 sha256sum -c`)
2. 並行 active session list 確認 (project-tree-manifest.md §3 active session list)
3. 自 node の親 node + 子 node の status 確認
4. 自 node の dependencies 状態確認 (precedent COMPLETE / blocker 解消)
5. 共通 file の sidecar pin 突合
6. 不整合検出時 BLOCKED_FOR_USER + rs 通知

**Sampling fallback 不採用 (v1.1):** v1 の sampling fallback は §4.4「全件 sha256 照合」と矛盾、integrity guarantee を degraded させるため不採用。代わりに parallelize で cost 削減 (1 node 全 file 通常 < 250 ms)。

**Atomic write 強制 (v1.1):** state.md / manifest への全 write は tempfile + `mv` で実装、reader が torn write を観測しない。

---

## §6 既存 task の移行 protocol

### §6.1 移行範囲

| task 状態 | 適用 |
|---|---|
| **既存 COMPLETE / ARCHIVED** | retroactive 適用なし、root node として manifest 登録のみ |
| **既存 active (IN_PROGRESS / HOLD)** | 次 milestone から段階適用 |
| **新 task** | 起動時から完全準拠 |

### §6.2 既存 task 段階適用手順

**対象**: 11-Env-Refactor / 12-Cable-Lift / RobotTAS v1 / DA-MPPI M4 等の active task

1. project-tree-manifest.md に root node 下の child として登録
2. 各 task の現 phase 完了時に node 構造化 (state.md front matter 整備、children mapping)
3. 次 phase 起動時から本 rule 完全適用 (handoff / completion / cascade rule)

### §6.3 移行期 (実証ベース、1-2 ヶ月想定だが固定しない) の混在許容

- 旧方式 task と新方式 task が混在
- 共通 file (handoff.md / SOMA.md / CLAUDE.md) は新方式準拠
- 個別 task の DEFINE は旧 format 維持可、ただし state.md 新 format 必須
- 期限超過時は rs 判断で延長 / 強制完了

---

## §7 root node + project-tree-manifest

### §7.1 root node の定義 (v1.1: 既存 L0 採用)

THREAD project の root node は本 v1.1 issuance 時点で `project_strategic_task_master_list_v2_2026-04-27.md:13` に記述された L0 を採用:

```yaml
root_node_id: T-ROOT
root_goal: 5-clip cable routing を vision-based で 95% 成功率達成
root_goal_source: project_strategic_task_master_list_v2_2026-04-27.md:13
root_goal_confirmed_by: rs (2026-04-27)
```

rs が後日 root_goal を改訂したい場合は §8.1 root 変更手順を適用。本 v1.1 は dormant 状態を持たず、issuance と同時に発効可能 (CLAUDE.md cross-ref 追加が前提条件)。

### §7.2 project-tree-manifest.md format

```yaml
---
title: THREAD Project Tree Manifest
created: 2026-04-27T00:00:00+09:00
last_updated: 2026-04-27T00:00:00+09:00
root_node_id: T-ROOT
root_goal: 5-clip cable routing を vision-based で 95% 成功率達成
---

# Manifest

## §1 Tree 構造 (text)
T-ROOT (5-clip vision 95%)
├── T-08 (DA-MPPI)
│   ├── T-08-1 (Stage A)
│   └── T-08-2 (Stage B)
├── T-09 (RobotTAS v1)
└── T-11 (Env Refactor)

## §2 全 node list
| node_id | name | parent | status | session active |
|---|---|---|---|---|

## §3 active session list (並行 CC 干渉防止用)
| session_id | node_id | host_pid | started_at | last_heartbeat |

## §4 dependency graph (依存関係 explicit、cross-tree dependent scan 用)

## §5 archive list (DISCARDED + ARCHIVED + COMPLETE、依存解決用 status snapshot 保持)
```

**注 (v1.1):** §3 active session list の更新は §5.2 Tier 2 (parent-mediated queue) で実施、CC 直接 manifest write 禁止。**（v1.2 部分改定 — §2 GEN 領域は生成器経由のみ可、§5.2 直後の v1.2 注記参照。2026-07-02 Rs A3 承認）**

---

## §8 失敗 / edge case の対応

### §8.1 root node の goal 変更

- root goal の変更は project 全体の re-design、rs 主観判断
- 既存全 node を再評価、不適合 node は DISCARDED 移管 + 新 means 再構築
- batch protocol: ≤20 nodes per wave、影響半径 (touched subtree) 優先、re-eval SLA ≤ 2 weeks

### §8.2 node 設計時の anti-pattern 警告

以下は anti-pattern、避ける:

- goal が 1 文で記述不能 (粒度過大、子 node 分割要)
- goal が「~を頑張る」「~を改善」など検証可能条件なし
- means が「rs に確認」のみ (rs 判断 node は許容するが、明示 rule 適用)
- children_nodes が 10+ 個 (構造設計再考要、中間 node 挿入推奨)

**検出責任 (v1.1):**
- 構造的 anti-pattern (goal 文長、children count) → deterministic precondition check at node-start (script ベース、Claude attention 不要)
- content anti-pattern (goal phrasing、検証可能性) → Claude Layer 2 review (§3.1 #4 起動承認時)

### §8.3 並行 CC 衝突発生時の復旧

1. 衝突検出 (sidecar hash mismatch)
2. 即 BLOCKED_FOR_USER
3. 衝突主体特定: PID registry (manifest §3 active session list の `host_pid` field) + `_pending_index.txt rs_disposition_log` 解析
4. 衝突対象 file の保全 backup (候補 session を SIGSTOP で quiesce 後に snapshot)
5. 復旧 path: vault 復元 / 引き継ぎ artifact 再構築 / node 完了不能判定 のいずれか rs 判断

---

## §9 本 rule の更新 protocol

- 本 rule の改訂は L3 cascade per CLAUDE.md §0「L3 自動昇格キーワード」+ §運用 25 (5-CC Pre-Debate) + §運用 15 Layer 2 post-Debate
- version 表記: `LTM-1 v1.1` → `LTM-1 v1.2` / `LTM-1 v2` (semver)
- 既存 active session への適用: 次 handoff 時から新 rule 適用 (現 session は前 version 維持、14 日以内 handoff mandatory)
- 改訂時の backward compatibility: 新規 mandatory field は read-optional (parser default None) で legacy artifact を refuse しない

**注 (v1.1):** v1 の「本 rule 自身も node として管理 (T-PM-LTM-1)」recursive structure は削除。global CLAUDE.md update protocol (`~/.claude/CLAUDE.md` の Bootstrap 注記) で代替。

---

## §10 Cross-references (v1.1: SSOT 参照拡充)

- **`project_nest_architecture.md`** (memory): NEST architecture 名称定義 + Components 概要 + versioning、本 rule の architecture-level reference
- **CLAUDE.md** (`/home/rlrk/IsaacLab/CLAUDE.md`): project-wide governing rule、§0 抵触時優先順位 canonical
- **prohibited.md** (`/home/rlrk/IsaacLab/.claude/rules/prohibited.md`): 禁止事項詳細、§3.4 プロセス kill 関連で参照
- **userMemories**: rs/Claude/CC 役割定義 + self-imposed rule
- **`~/.claude/hooks/lib/ctx_thresholds.sh`**: context window threshold (FLAG_WRITE / SOFT / HARD / STALE_SECONDS) の SSOT、§4.3 で参照、本 rule では値再記述しない
- **`feedback_subsession_notifyback_protocol.md`**: per-session signal file pattern の SSOT、§5.2 Tier 1 で採用
- **`feedback_autonomous_kill_authorized.md` / `feedback_autonomous_vault_update_authorized.md` / `feedback_autonomous_execution_absent_rs.md`**: rs/CC permission cascade、§3.4 で参照
- **`thread-vault/02-Workflow/Vault Write Permissions.md`**: directory-level write permission matrix、§5.2 で補完関係
- **`feedback_user_options_max_3.md`**: 本 session 派生 rule (user 選択肢 2-3 max)、NEST 命名 session 後半で確立
- **本 rule 起源**: rs 提案 2026-04-27 (ロジックツリー管理 + node = session + cascade + 引き継ぎ機構)
- **5-CC Pre-Debate (2026-04-27)**: v1 → v1.1 brush-up、CRITICAL 5 件 fix + 22 P-item v3 defer
- **NEST 命名 (2026-04-27)**: NEST / CASCADE-LT / GROVE の 3 候補から Rs 採択

---

## Appendix A: v3 defer 一覧 (post-deployment empirical motivation で個別採用)

以下の 22 P-item は本 v1.1 では採用せず、v1.1 deployment 後に empirical incident で motivate された時点で個別 v3 で採用検討:

| Pxx | Topic | 何故 v3 defer |
|---|---|---|
| P1 (一部) | 用語拡充 (cascade / hash_pin / priority / effort) | dependency 2-edge 化のみ v1.1 採用、他は使用 context が現れてから |
| P2 (一部) | state.md priority/risk_register/estimated_effort field | NHA SD-3 + KA-6 (Option X-2 priority 委譲)、empirical 必要性なしで採用しない |
| P3 (一部) | PENDING→HOLD transition | CC2-4 で REJECTED、defer not needed |
| P4 (一部) | Soft/Hard cancel terminology | CC2-9 で「§3.2 means abandonment」に re-frame、separate defer 不要 |
| P5 (一部) | force-COMPLETE warning + cross-tree cascade | §3.5 + §3.4 step 5 で v1.1 部分採用 |
| P11 (一部) | parallel session bound | empirical bound 観測後に追加 |
| P14 | 「次 milestone」task DEFINE 内定義 | task ごとに自然に定まる、明文化は v3 |
| P15 | 1-2 ヶ月期限の deadline / extension | empirical extension trigger 観測後 |
| P17 | CC 自身が manifest update | §5.2 Tier 2 で reconciliation 経由、direct write は永久禁止 **（v1.2 注記 [§5.2 配下] により部分改定: §2 GEN 領域のみ生成器経由の CC 再生成可。2026-07-02 Rs A3 承認）** |
| P18 | root 変更 5 step 詳細 | §8.1 で batch protocol 概略のみ採用、5 step 詳細は v3 |
| P19 | anti-pattern detection 起動 block | §8.2 で検出責任 split、enforcement script は v3 |
| P21 | rule 改訂時の v1/v2 mixed handling | §9 で 14 day handoff mandatory + read-optional のみ採用、詳細 backward compat policy は v3 |
| P22 | cross-ref 抵触時優先順位重複明記 | §0 single source、§10 重複は DRY 違反、不採用 |
| P24 | 新 §11 priority/effort/risk register | NHA KA-6 で Option X-2 priority 委譲、不採用 |
| P25 | rs ABORT / HALT signal-level extension | §3.4 で CLAUDE.md §運用20 + prohibited.md cross-ref のみ、ABORT vocabulary 拡張は v3 |
| P26 | 新 §13 scalability constraints | empirical bound 観測後 |
| P28 (詳細) | transition overlap protocol session_state | §5.1 で session_state 4-state 採用、詳細 lock hierarchy は v3 |
| P29 | manifest archive 自動分離 | empirical archive 累積観測後 |
| P30 | spawn dependency 4th edge | §1 注で trace 関係に明記、edge 化は不採用 |
| その他 | (CC2-7 6×6 matrix, CC3-9 nanosecond timestamp 等) | 採用 cost > 効用、defer |

---

**End of LTM-1 v1.1 patch.**

**rs review 要請**:
- Path D 採用結果 (CRITICAL 5 fix + minor 2 + cross-ref 1) が rs 期待と一致するか
- §7.1 root_goal 「5-clip cable routing vision-based 95%」を本 rule の root として採用可
- §10 cross-ref 追加 SSOT (ctx_thresholds.sh, feedback_subsession_notifyback_protocol.md, Vault Write Permissions.md) で過不足ないか
- Appendix A の v3 defer 22 P-item で見落としあれば指摘
- v1.1 deploy 前に CLAUDE.md への cross-ref 追加 (L3 cascade) を併せて実施するか

確認後、本 v1.1 を vault `00-Project-Management/operational-rule-LTM-1.md` に deploy + project-tree-manifest.md (root_goal 確定版) を作成可能。
