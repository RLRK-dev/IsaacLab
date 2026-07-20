# 未 commit の `CLAUDE.md:72` が約 36h 全 session を統治していた件 — attestation

**Recorder:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**記録:** 2026-07-21 02:36 JST。
**契機:** p6 の CLAUDE.md 履歴 finding (`a58983582f`) への独立確認中に判明。
**⚠ 本書の一次的価値 = git から復元できないテキストの逐語保存**（下記 §3）。

## 1. 事実 — 4 面のうち 1 面だけが「例外 0」と言っていた

| 面 | 状態 | kinematic 例外の扱い |
|---|---|---|
| `CLAUDE.md` **committed 履歴** | `35029056bd^`:72 実測 | ✅「**唯一の認可例外 = clip-retention pin**」 |
| `.claude/rules/prohibited.md` | ⚠**git 管理外（untracked）**・mtime 07-19 07:29:13 以降不変（**v1.1 訂正** — 下記 §1-1） | ✅「**唯一の認可例外 = clip-retention pin（§0#5）**」（as-read） |
| `RS71-System-Spec-SSOT.md` §0#5 | `:27` / `:28` | ✅「the ONLY authorized exception is the clip-retention pin」＋ **07-15 Rs 逐語「クリップのみ pin を RL env に恒久配線しろ」** |
| ⛔ `CLAUDE.md:72` **working tree（未 commit）** | 全 session に auto-load | ⛔「**kinematic 例外は 0 件**」 |

⇒ **統治文書 4 面のうち 3 面が一貫して pin 例外を認めており、唯一の反対者が「未 commit の編集」だった。**
そしてその 1 面が、実際に全 session の context を統治していた。
⚠ **ただし「3 面」のうち `prohibited.md` の一致は *as-read* に限る** — producing commit での verify が原理的に不可能（§1-1）。

## 1-1. ⚠ v1.1 訂正 — `prohibited.md` を「committed・clean」と書いたのは誤り（p6 指摘 02:40）

**v1.0 の記載**:「`prohibited.md` = **committed・clean**（`git status` 空）」⇒ ⛔**FALSE**。

**実測（p6 指摘を独立再現）**:

| 検査 | 結果 |
|---|---|
| `git ls-files .claude/` | **0 件** — `.claude/` 配下は **tracked が 1 つも無い** |
| `git check-ignore -v` | `.gitignore:101:/.claude/` に一致 = **ignored** |
| `git cat-file -e 35029056bd^:.claude/rules/prohibited.md` | **存在しない**（当該 commit に file 自体が無い） |

⭐ **私の誤りの機序 = 「空の出力」を 1 通りにしか読まなかった。**
`git status --porcelain <path>` は **clean でも ignored でも空**を返し、**両者を区別しない**。
私は空を見て「clean」と結論した。⇒ **述語が 2 状態を判別できないのに、負の結果を一方の確証として読んだ。**

⛔ **さらに悪いことに、私は反証を手に持っていた。** `git show 35029056bd^:.claude/rules/prohibited.md`
に grep をかけて 0 hit だった時、私はそれを「grep pattern が合っていない」と処理して先へ進んだ。
**正しい読みは「その commit に file が無い」**だった。**負の結果の原因を、確かめずに自分に都合よく帰属させた。**

⚠ **本件は、私が本 session で 3 度診断してきた欠陥クラス（`validate.sh` Layer 1-3 / NEST guard の membership 述語 /
未 commit 編集）と同型である** — **「述語が世界と一致していないのに、その出力を根拠として読む」**。
検証者が同じ型を踏んだ事実を、実例として記録する。

⭐ **訂正は finding を弱めず、強める（p6 の指摘・採用）**:
auto-load される rule 面 2 つのうち、**`CLAUDE.md` は未 commit 編集に統治され、`prohibited.md` は git 管理外**。
**後者は編集しても diff も履歴も dirty 表示も残らない** ⇒ **未 commit 編集よりさらに追跡困難**で、
**provenance は mtime のみ**。⇒ **「一貫して pin 例外を認めていた」は on-disk as-read としては真だが、
`prohibited.md` については いかなる producing commit でも verify 不能**。
（mtime `07-19 07:29:13` = `a97c3fe43d`（07-19 07:32）の 3 分前 ⇒ **同一編集窓と整合** という p6 の観察は有効。）

**self-sweep（同クラスの掃き出し）**: 本 session で私が引いた他の面はすべて tracked を実測確認 —
`RS71-System-Spec-SSOT.md` / `00-DESIGN-STATUS-LEDGER.md` / `CLAUDE.md` / `task_config.py` = **すべて tracked=1**。
⇒ **同型の誤りは `.claude/` 配下の 1 件に限局**しており、他の verdict へは波及しない。

## 2. 統治していたことの attestation（3 pane・3 時点で独立）

| # | 観測者 | 時刻 | 観測内容 | 出典 |
|---|---|---|---|---|
| 1 | **pN** (OPS-SUP-CODEX) | **2026-07-19 18:16** | 逐語「`:72` = **kinematic 例外 0 件**・body state 直接駆動禁止」 | `00-DESIGN-STATUS-LEDGER.md` §DDR #25（p6 が所在を特定） |
| 2 | **pY** (本 pane) | **2026-07-21 00:17** | session 起動時 auto-load の `CLAUDE.md:72` が「kinematic 例外は 0 件」を含む（§3 に逐語） | 本 session の system context |
| 3 | **p6** (PLAN-KEEPER) | 2026-07-21 02:2x | committed 履歴に当該文字列が無いことを実測し矛盾を検出 | `a58983582f` |

⭐ **#1 の意義**: p6 は従来 pN のこの記述を「committed と矛盾するので誤読か」と疑っていた。
**pN は未 commit 版を正確に読んでいた**と解すと整合する ⇒ **pN の記述は誤読ではなく、正しい観測だった**（名誉回復）。
⇒ 統治窓 = **少なくとも 07-19 18:16 → 07-21 02:05**（`35029056bd` が同 region を書換）。

## 3. ⭐ 逐語保存（git から復元不能・本書が一次記録）

pY が 2026-07-21 00:17 に auto-load で受領した `CLAUDE.md:72` の逐語:

> - 〔上記のうち *具体 API 名*（`DifferentialIKController`/`write_joint_*`/`set_joint_*`）は PhysX 実装形。**不変前提「IK 制御のみ・kinematic トリック（物理無視の強制配置＝アーム関節角の直接書き込み等）禁止・制御方式変更は Rs 承認」は全 substrate 共通（§0#3/#5、`validate.sh` Layer 8 が機械検証）**。**kinematic 例外は 0 件**であり、clip-retention pin / weld / cable・finger attachment / arm・body state 直接駆動も禁止する（Rs 「kimenatic 完全削除」2026-07-19）。Newton の対応 API・制御制約は `thread-vault/06-Knowledge/LL-Newton.md` 参照〕

**復元不能性の検証（p6 の推測を検証した結果 = 支持）:**

| 手段 | 結果 |
|---|---|
| `git log --all -S"例外は 0 件" -- CLAUDE.md` | **0 commits** |
| `git log --all -G"例外は 0 件" -- CLAUDE.md` | **0 commits**（独立 2 方式一致） |
| `git stash` | 1 entry のみ・無関係（"Isaac Sim 6.0 migration" 由来）・当該文字列 **0** |
| `git fsck --lost-found` dangling blob 走査 | ⚠**timeout により未完**（repo 規模）。**「無い」とは言えない** — 本レグは **未完了**と明示する |

⇒ **通常経路では復元不能**。dangling blob の全走査は未完のため「絶対に存在しない」とは主張しない。
**現時点で確実な一次記録は、本書 §3 の逐語（pY session 観測）と、pN の LEDGER 記述の 2 つ。**

## 4. 含意（記録・裁定しない）

1. ⭐**L3 file が commit なしで実効的に改訂された。** L3 gate・review・provenance・rule-check のいずれも通っていない。
   `CLAUDE.md` は project の最上位 rule file であり、**変更は L3 自動昇格対象**（`CLAUDE.md` §0 自身が規定）。
   **未 commit 編集はこの gate を構造的に迂回する** — diff が git に現れないため、いかなる自動検査も発火しない。
2. ⭐**auto-load される 2 面（`CLAUDE.md` / `prohibited.md`）が約 36h 互いに矛盾していた。**
   同一 session context 内に「例外 0」と「唯一の例外 = pin」が同時に存在した。
   ⇒ 受け手（各 pane）はどちらを採るかを暗黙に選ばされていた。
3. ⇒ **census 35 除去 arc の authority は `CLAUDE.md` ではなかった**（p6 の結論を支持）。
   committed rule file は一貫して pin 例外を保持していたので、arc を駆動したのは
   **Rs directive（pN relay）＋ vault 面＋この未 commit 編集**である。
4. ⭐**Rs 裁定 B（2026-07-21 01:3x）は、4 面のうち 3 面が既に述べていた状態へ全体を戻すもの**であり、
   **committed spec 群と整合する方向**の変更である（`STEP43_C69_EVIDENCE_READBACK_OPSSUP_20260721.md` §B-2 と同結論）。

## 5. 非主張

- ⛔ 誰が・なぜ未 commit 編集を行ったかは**不明**。本書は帰属を主張しない。
- ⛔ dangling blob 走査は**未完**。復元不能は「通常経路で」の限定付き主張。
- ⛔ 本書は記録であり、rule file の編集・guard の変更・class 裁定を行わない（いずれも別 owner）。
- ⛔ `CLAUDE.md` は L3 ゆえ CC 編集不可。訂正要請は owner（Rs / p4）へ。

---
**記録 = 2026-07-21 02:36 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
