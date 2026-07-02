# operational-rule-LTM-1 v1.2 差分案

## ステータス

- 状態: WITHDRAWN / 非昇格 (2026-05-31、Rs directive C — Neumann trial CLOSED、v1.2 へ昇格せず。価値ある原則は informal retain、正式 codification は別途 Rs+L3。根拠: `KN-Method-Neumann-on-NEST.md` レビュー記録 2026-05-31)
- ⚠ label collision note (2026-07-02): 「LTM-1 v1.2」の版番号は **2026-07-02 landed の GEN-region 注記 (Rs D3)** が使用済み。本 WITHDRAWN 案は別内容の旧 v1.2 案であり、復活させる場合は **v1.3+ を採番**すること。
- 作成: 2026-05-05
- 対象 SSOT: `thread-vault/00-Project-Management/operational-rule-LTM-1.md` (`LTM-1 v1.1`)
- 根拠ノート: `thread-vault/06-Knowledge/KN-Method-Neumann-on-NEST.md`
- 発効条件:
  1. `KN-Method-Neumann-on-NEST.md` の trial 成功
  2. Rs が `LTM-1 v1.2` 改訂判断
  3. L3 cascade (`5-CC Pre-Debate` + post-debate) 通過
- 非目標:
  - 本ファイル単体では rule を発効しない
  - `CLAUDE.md` の即時更新を前提にしない
  - 系2「構成的単一提案」を本書で norm 化しない

## 採用方針

- `v1.1` の core lifecycle / status taxonomy / dependency 2-edge / cascade rule は維持する。
- `N0` から `N8` のうち、NEST の node 定義・完了判定・handoff artifact に直接かかるものだけを `v1.2` 候補とする。
- 追加 requirement は `v1.2` 以降に新規起票される node に適用し、legacy node artifact は `read-optional` とする。
- `rs` のみが tree write を行う原則は維持する。CC は観測・提案のみを行う。
- trial note にある `P5 tree restructure` は既存 `§3.5 cascade rule` の gate を利用し、新たな権限モデルは追加しない。

## 差分サマリ

| 対象節 | 変更種別 | 要旨 |
|---|---|---|
| `§2` | 追加 | `DEFINE-*.md` に semantic contract を導入 |
| `§3.1` | 追記 | 起動条件に `Atoms / Out / Work-Range / success criteria` を追加 |
| `§3.2` | 追記 | provisional axiom drift の記録経路を明示 |
| `§3.3` | 追記 | `COMPLETE` を `Work-Range` 束縛にし、`Concrete-Return` を完了前確認項目に追加 |
| `§4.2` | 追記 | handoff artifact に `NEST_PROPOSALS` appendix を追加 |
| `§9` | 追記 | backward compatibility を `v1.2` semantic contract に明示適用 |

## 候補差分

### Patch 1: `§2` に semantic contract 節を新設

配置案: `§2.3 state.md の必須 front matter` の後に `§2.4` を追加。

```md
### §2.4 DEFINE semantic contract (v1.2 candidate)

`v1.2` 以降に新規起票される node の `DEFINE-*.md` は、`goal` / `means`
に加えて以下の semantic contract を持つ。

1. **Phenomena**: この node が扱う観測・制約・失敗例
2. **Model**: それを扱う数学的・構造的・手続的モデル
3. **Interpretation**: model の各要素が実務上何を意味するか
4. **Work-Range**: どの範囲で「機能した」と見なすか
5. **Atoms**: 扱う最小要素集合
6. **Out**: 範囲外要素
7. **Success criteria**: 以下の少なくとも 1 つ
   - coverage
   - robustness
   - transfer
   - heterogeneity
   - work_range
8. **Analogy search**: 構造類似検索の hit または no-hit 記録

以下は条件付き mandatory:

- **Simplicity guard**: 「単純化」が採用理由に含まれる場合
  - Simplicity
  - Explained-Range
  - Tradeoff
- **Conceptual clarity**: 新しい用語・判定軸・精密な手順を追加する場合
  - Term
  - Boundary
  - Use
  - Failure

本 contract は final axiomatics ではなく provisional axiomatics として扱う。
trial 後に drift が観測された場合、silent overwrite ではなく `§3.2` の drift
経路で扱う。
```

テンプレート案:

```md
## Semantic contract

- Phenomena:
- Model:
- Interpretation:
- Work-Range:
- Atoms:
- Out:

## Success criteria

- coverage:
- robustness:
- transfer:
- heterogeneity:
- work_range:

## Analogy search

- query_shape:
- hits:

## Simplicity guard  # 条件付き

- Simplicity:
- Explained-Range:
- Tradeoff:

## Conceptual clarity  # 条件付き

- Term:
- Boundary:
- Use:
- Failure:
```

設計判断:

- `state.md` front matter は `v1.1` のまま維持し、verbose な意味論は `DEFINE-*.md` に寄せる。
- これにより parser 変更を最小化しつつ、`N0/N1/N2/N3/N4/N8` を formalize できる。

### Patch 2: `§3.1 node 起動` に semantic contract gate を追加

`起動条件` の `goal` 記述 requirement の直後に以下を追加する案。

```md
4. `DEFINE-*.md` の semantic contract が記述済
   - `Phenomena / Model / Interpretation / Work-Range / Atoms / Out`
   - `Success criteria` 少なくとも 1 件
5. `Analogy search` の hit または no-hit が記録済
6. rs 承認 (起動承認、子 node 作成承認とは別 gate)
```

補足:

- `v1.1` node や `v1.2` 前に起票済の active node には retroactive 強制しない。
- `N3` は tooling mandatory にせず、`manual grep` を含む record mandatory とする。

### Patch 3: `§3.2 node 進行中の操作` に drift 処理を追加

`session 中に発生する操作` に以下の bullet を追加する案。

```md
- **provisional axiom drift**: `Atoms / Out / Success criteria / Work-Range`
  と empirical state の不一致を観測した場合、CC は `session_history` と
  handoff artifact に evidence を残し、次のいずれかで処理する
  - P4: 条件追加 / 緩和 / 廃案の提案
  - P3': 当 node の DISCARD 提案 + 新 node 起票提案
  - P5: tree restructure 提案 (`§3.5` + L3 cascade)
  silent in-place rewrite は禁止
```

設計判断:

- `N5` は新しい status や権限を導入せず、既存 lifecycle 上の proposal path として扱う。
- `P3` in-place 修正は採らない。`DISCARDED -> IN_PROGRESS` 禁止 (`§3.7`) と整合する。

### Patch 4: `§3.3 node 完了` に Work-Range / Concrete-Return を追加

`完了条件` と `完了手順` に以下を追記する案。

```md
**完了条件 (追加):**
5. COMPLETE 判定が declared `Work-Range` 内の成功として説明できる
6. node が抽象化・一般化を含む場合、少なくとも 1 件の
   `Empirical-Source / Concrete-Return` 対応が記録済

**完了手順 (追加):**
8. closure log に以下を統合
   - Work-Range 内で何が成功したか
   - Out に戻す範囲は何か
   - Empirical-Source
   - Concrete-Return
   - Degeneration-Check
```

設計判断:

- `N2` の成功基準は `goal_verification` を置き換えず、補完する。
- `N6/N7` は「COMPLETE = 絶対真理」を避け、range-bound verdict にする。
- `Concrete-Return` は全 node に一律 mandatory ではなく、抽象化を含む node に限定する。

### Patch 5: `§4.2 handoff artifact format` に `NEST_PROPOSALS` appendix を追加

現行 `§1` から `§7` の必須 section は維持し、`optional appendix` を追加する案。

```md
## §8 NEST_PROPOSALS (optional, Rs review only)

CC が node 実行中に構造的提案を観測した場合、handoff artifact 末尾に以下を記録できる。
本 appendix は tree write 権限を与えず、Rs review queue としてのみ機能する。

### P1: child node 候補
- node_id 案:
- goal:
- means:
- 発生根拠:
- Atoms 案:
- Out 案:
- Success criteria 案:

### P2: N3 構造類似ヒット
- 自 node 構造:
- 類似 COMPLETE node:
- 同型部分:
- 流用候補:

### P3': DISCARD + 新 node 起票提案
- 当 node status:
- 新 node 案:
- provenance:
- 根拠:

### P4: success criteria drift 警告
- 当初条件:
- 観測上の困難:
- 提案:

### P5: tree restructure
- 提案内容:
- 必要根拠:
- L3 cascade 必須認識:
```

設計判断:

- `NEST_PROPOSALS` は `v1.1` でも運用可能だが、`v1.2` では appendix として formalize する。
- `P5` は新しい近道を作らず、既存 `§3.5` と `§9` の gate に従う。

### Patch 6: `§9 本 rule の更新 protocol` に compatibility 注記を追加

`backward compatibility` の bullet の後に、以下を追加する案。

```md
- `v1.2` semantic contract は新規 node に対して mandatory、legacy node は
  read-optional とする。既存 active node は次 handoff 以降に必要部分のみ
  backfill すればよく、retroactive full rewrite は要求しない。
- parser / audit script は `DEFINE-*.md` 内の新 section 欠落を即 invalid とせず、
  `unknown` / `not_recorded` として扱う。
```

## 明示的に defer する項目

- 系2「構成的単一提案」
  - `CLAUDE.md §運用26` 側の運用変更を伴うため、本差分案から除外
- `N3` 自動検索 tooling
  - `manual grep` または将来の `rag_query_vault.sh` 拡張で扱う
- `userMemories precedence formalize / Bootstrap time boundary / bidirectional cross-ref`
  - `nest-adoption-runbook.md` の `F7 (defer)` 系であり、本 Neumann 由来差分とは分離
- `T-ROOT` 寄与宣言
  - trial note で drop 済、`v1.2` 候補に含めない

## 明示的に変えない項目

- `status` taxonomy (`PENDING / IN_PROGRESS / HOLD / COMPLETE / ARCHIVED / DISCARDED`)
- dependency taxonomy (`precedent / blocker`)
- `§3.5 cascade rule`
- `§5` 並行運用 protocol
- `rs` の tree write 独占

## L3 debate で詰めるべき論点

1. semantic contract の mandatory 範囲を `DEFINE-*.md` に限定するか、`state.md` にも要約を持たせるか
2. `Concrete-Return` の適用条件を「抽象化を含む node」にするか、「全 node」に広げるか
3. `NEST_PROPOSALS` を `optional appendix` に留めるか、handoff 時の `recommended` まで上げるか
4. `Simplicity guard` と `Conceptual clarity` を条件付き mandatory に留めるか、全 proposal node に広げるか

## 位置づけ

本ファイルは `LTM-1 v1.2` そのものではない。`KN-Method-Neumann-on-NEST.md` の
trial が empirical に支持された場合にのみ、L3 cascade の input として使う
separate diff proposal である。
