# 裁定 B の表現統一 — canonical wording（custody record）**v1.1**

**Recorder:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**v1.0** = 2026-07-21 02:52 / **v1.1** = 03:04（**canonical を訂正**）。
**契機:** pY が c69 readback (`526ae65bed` §C) で提起した custody OPEN への Rs 回答。

⛔⛔ **下流へ: v1.0 の canonical は SUPERSEDED。適用済みの面は v1.1 へ差し替えを要します**
（pX `0f7aaaea56` が v1.0 を適用済 — pY から即時通知）。

## Rs 逐語（2026-07-21 02:4x、2 段）

> ①（2 表現を示して）**この2つは同じことを意味している**
> ②**1つに統一した表現にして**

## ⭐ CANONICAL WORDING（v1.1・本 record が SSOT）

> **kinematic の唯一の認可例外 = `clip-retention pin`
> （＝ **clip 側がケーブルを保持する機構**。⚠ **gripper の把持ではない**）**

⛔ 不許可（併記必須・不変）= **腕関節角の直接書込 / 指の kinematic close / `update_kinematic_bodies`（FK→physics の body 複写）/ weld・cable-finger attachment**。

⚠ **「pin 復活 = kinematic 復活」ではない。** 例外は上記 1 件のみ。

## 1. ⚠ v1.1 訂正 — v1.0 の gloss は工程表の語と衝突していた（p4 指摘・採用）

**v1.0 の canonical**:「`clip-retention pin`（クリップの**ケーブル固定**）」⇒ ⛔**gloss が不適**。

**理由（実測）**: `RL-Routing-Design.md:1312` step 12 の行は
「… | クランプ | アンクランプ | C1 | **左クランプ（ケーブル固定）** |」であり、
左右列は **gripper の状態**（クランプ / アンクランプ / 半アンクランプ）。
⇒ **工程表において「クランプ」「ケーブル固定」は *gripper がケーブルを掴む動作* を指す語**。
⇒ v1.0 の gloss は、**本例外（clip 側の保持）を gripper 把持と読み違えさせる**。

⭐**訂正後の gloss は「どちら側が保持するか」を明示する** — これが実際に区別すべき意味軸である。
`clip-retention pin` という英語名の選定（16 occ / 4 file・`RS71 §0#5` の不変前提名）は**不変**であり、
pX が独立に census を再実測して再現済（`0f7aaaea56`）。**変えたのは日本語 gloss のみ。**

## 2. ⛔ v1.0 の選定根拠表にあった 2 つの誤り（pY 自己申告）

| # | v1.0 の記載 | 実測 | 機序 |
|---|---|---|---|
| ① | 適用表で `CLAUDE.md:72` が旧語を保持していると記載 | ⛔**stale**。c72 `c2bcde7428` **02:24** で除去済 = 本 record 執筆（02:52）の **28 分前** | 上流が動いた面を、読んだ時刻を確かめずに現在形で書いた |
| ② | 旧語の 1 occurrence を `CLAUDE.md:72` 由来と記載 | ⛔**誤帰属**。実際は `00-DESIGN-STATUS-LEDGER.md:35`（受領 receipt）。`CLAUDE.md` = **0** | `grep -rl` / `-rho` は**ファイル名を捨てる**。集計値を、確認せずに特定の member へ帰属させた |
| ③ | 頻度（9 occ）を gloss 適合の根拠にした | ⛔**意味を区別していない**。当該語は工程表で **gripper 把持**の意味を持つ（§1） | **文字列一致という述語が 2 つの語義を判別しないのに、集計を一方の支持として読んだ** |

⭐ **①②③ は同一の型**であり、**本 session で pY が 3 度目に踏んだ同じ family**（1 度目 = `git status` 空を clean と読んだ〔実は ignored〕）。
共通形 = **「述語が世界を判別しないのに、その出力を根拠として読む」**。
本 session で pY が他者に対して 4 度診断した欠陥クラスと同型である。**検証する側が最も踏む。**

## 3. 適用（surface 別・v1.1 時点で実測）

| surface | 状態 | 要処置 | owner |
|---|---|---|---|
| `CLAUDE.md:72` | 旧語は c72 で除去済。現行は p4 造語「clip 側がケーブルを保持する機構」 | ⭐**v1.1 canonical と実質同義** ⇒ 残差は **`update_kinematic_bodies` の不許可列 明示**のみ | Rs / p4（**L3・CC read-only**・diff 提示中） |
| `c69 §9` | c75 `b2bd3bde99` で canonical 併記 + 逐語節を受領記録として再ラベル済 | **v1.1 gloss へ更新** | p4 |
| `LEDGER:35` / DDR#25 carry④ | pX `0f7aaaea56` が **v1.0 を適用済** | ⛔**v1.1 へ差替え要** | pX / p6 |
| memory（`project-sim-is-reality-no-kinematic-20260719` / `MEMORY.md`） | v1.0 適用済 | **v1.1 へ更新** | pY |
| `RS71 §0#5` | 既に canonical（英語名） | **編集不要** | — |

## 4. ⭐ 逐語 receipt は統一の対象外（pX 指摘・採用）

**統一は「規範文」にのみ適用する。U1 / U2 の逐語 receipt には適用しない。**
Rs が統一を指示したのは**規範の語**であって、**発話の記録**ではない（pY の非主張とも整合）。
⇒ ⛔**後日の語彙 sweep で quote を正規化しないこと。**
⚠ 同じ receipt が、**削除要請**と**語の統一**という別々の圧力で 2 度失われかけている（pX 記録）。保存理由を面に併記すること。

## 5. ⭐ 計数記述の恒久ルール（pX 発・採用）

**計数・不在・census を書くときは、対象語を literal に書かない**（記述自体が計数を変え、報告が自己を偽にする）。
pX が本日 2 度目の self-inflation を踏み（同 file の計数が 1→3 になった）、DDR#34 の接頭辞問題と同型として恒久ルール化。
⇒ **本 record 本文もこの規則に従い、旧語を literal に列挙していない。**

## 非主張

- ⛔ どちらが literal な Rs 発話かは**未確定**。Rs が確定させたのは**同義性**と**統一指示**であって逐語の指定ではない。
- ⛔ 本 record は裁定 B の**適用範囲**を変更しない（範囲 = `c69 §9` の表・Rs「ok」で確定済）。**語の統一のみ。**
- ⛔ `CLAUDE.md` は CC 編集不可。pY は差替えを**提案**するのみ。

---
**v1.1 記録 = 2026-07-21 03:04 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
