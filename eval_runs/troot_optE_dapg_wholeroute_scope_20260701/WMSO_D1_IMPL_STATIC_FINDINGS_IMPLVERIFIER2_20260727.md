# WMSO D1 実装 — 静的読解による findings（IMPL-VERIFIER2 / w2:p15）

## ⭐ 追記（2026-07-27 20:0x JST）— Finding B は「候補」→「実在」に確定

⛔ **本書は依然として verdict ではありません**（下の §「これは verdict ではありません」は有効）。⛔ **修正は行っていません**（fix は gate 開放後に p14）。⛔ **LEDGER / status / planning 面も無変更**。⛔ **原文は 1 文字も消していません**（本節は append のみ）。

**何が変わったか**: 下の §Finding B は「候補（未確認）」と書いてあります。**その記述は、書いた時点（読解 2026-07-27 14:0x–14:2x JST）の私の証拠としては正しいまま**ですが、**その後 B は確定しました**。原文を残したまま、確定の事実をここに追記します。

- **一次確定 = p12**（p18 経由 relay `-343`。私の pane では 20:00:25 JST の測定より前に受信）: pattern 文字列のみを standalone 評価して `"a"*64 + "\n"` → True。精密化 = 通るのは**末尾改行 1 個のみ**、`fullmatch` で直る。
- **独立再測 = 私（p15）**: relay の数値を根拠にせず自分で測り、**一致を確認**。

### 私の測定（p12 発の read-only 測定則の 3 条件に従う）

- **① command / interpreter**: `/usr/bin/python3` に heredoc で stdin 供給（`isaaclab.sh` は不使用）。pattern は `contracts.py` から**機械抽出**（転記していない）→ 抽出値 `^[0-9a-f]{64}$`
- **② rc = 0**。⚠ その直前に **rc=1 の失敗が 1 回**あります（shell の quote による `SyntaxError`。測定値は出ていません）
- **③ 副作用**: import は stdlib `re` のみ・**project module は import せず**・file 書込 0・sim / GPU / network 不触
- **対象版**: `contracts.py` = `be24c30eda1b2907a872d50bccc7b668253d034f12256f053a0e3ee3d374c56c` — **追記時（2026-07-27 20:02:45 JST）に再測して同一を確認**。本書が引用する他 4 file も同時刻に再測し、全て同一でした（cached な接地を使っていません）。

| ケース | `match()` | `fullmatch()` |
|---|---|---|
| 64 hex | True | True |
| **64 hex + 改行 1 個** | **True（欠陥）** | **False（fix が効く）** |
| 64 hex + 改行 2 個 | False | False |
| 64 hex + 改行 + 文字 | False | False |
| 63 hex / 65 hex / 大文字 / 空文字 | False | False |

⇒ 「通るのは末尾改行 1 個のみ」も「`fullmatch` で直る」も、**私の測定で成立**します。

### Finding A について

p12 が識別可能な 5 綴りの query で独立確認 ⇒ **集合等値検査は不在＝実在・潜在**。

### 私の見積り誤り（記録として残す）

私は B の確認を「**実行が要るから保留**」としましたが、**pattern 文字列の評価だけで足りました**。実行の範囲を過大に見積もっていた、ということです。p12 発の一般則（read-only・in-memory・file / sim / GPU / network 不触の測定は CLOSED に当たらない。条件 = command と interpreter の明記・rc の明記・import 副作用の事前確認）で解消済みです。

### 追記の許可と sha

p18 の custody 裁定（relay `-348`。私の pane では 20:02:45 JST の再測より前に受信）= **追記して新 sha を宣言**。
**旧 sha** `de3cad3832aabf06e32b013080223c3b596d04de40aef4b5b41643b6f497237c` → **新 sha は本追記の bank 後に p18 へ 1 行で通知**します。

---

## ⛔ これは verdict ではありません（条件①）

本書は **判定（PASS / FAIL / PASS-CLOSE）ではなく、材料**です。理由:

- 私（p15 = IMPL-VERIFIER2）の担当は **p14（IMPL-BUILDER2）の実装の独立検証**です（brief `IMPL_VERIFIER2_ROLE_BRIEF_p15_20260727.md` @ commit `124b8cad70`）。本書が扱う `thread_isaac_lab/wmso/d1/` は **p14 の実装ではありません**。
- 本書の内容は、私の brief が着地する**前**（2026-07-27 14:0x–14:2x JST）に読解したものです。
- 記録の許可 = p12 の disposition（p18 経由 relay `-212`、2026-07-27 18:22 JST）。⛔ **本 disposition は記録の許可のみで、gate は一切開いていません。**

## 証拠クラスと射程

- **手法 = 静的読解のみ。** 対象 module を実行していません（実行を伴う検査は保留中）。
- **射程** = 下表の 5 file の**その版のみ**。他の版・他の file・実行時の挙動については何も述べていません。
- 観測時刻: 読解 = 2026-07-27 14:0x–14:2x JST / 版の固定（sha256 実測） = 2026-07-27 18:23:15 JST。
- 引用は **content sha256 で引きます**（行番号のみで引かない・条件②）。下表の 5 file はいずれも **worktree == HEAD**（実測）。

| file | content sha256 |
|---|---|
| `thread_isaac_lab/wmso/d1/contracts.py` | `be24c30eda1b2907a872d50bccc7b668253d034f12256f053a0e3ee3d374c56c` |
| `thread_isaac_lab/wmso/d1/harness.py` | `78015cabcf339f4ef37bb1e4c49fea299206f3c9db4c314d419b4d77963178fd` |
| `thread_isaac_lab/wmso/d1/identity.py` | `ca4aeababa88affaff6f410c5b1d4d64bf94667dc3f18ffd6945ee6acc0890d3` |
| `thread_isaac_lab/wmso/d1/tests/test_contracts.py` | `58641a87f560ff5e0b78068b5d8bf6beb2bef996eb98a8bc8708a9f7aea898f5` |
| `thread_isaac_lab/wmso/d1/tests/test_harness.py` | `e2612076dfbb0fc8462af7cd1818e850988f2ce32bc9600a6dfb1af0c38f093c` |

## ⭐ pN の step-5 PASS-CLOSE との関係（条件⑤）

本書の対象は、**pN が 2026-07-19 に impl-verify / reverify を回して PASS-CLOSE した面**です（参照 commit `57ed32b27a`、系列 = `23a83727c8` → `a400e7141b` → `1f436530a9` → `57ed32b27a`）。

⇒ **A と B が成立するなら、それは PASS-CLOSE 済の面に残っていた穴**にあたります。ここは明示しておきます。

⛔ ただし本書は **「pN が誤った」とは主張しません**。私は pN の step-5 が**どの述語を対象にしたか**を確認していないため、本書の 2 件がその対象範囲の内か外かを判定できません。**この扱い（矛盾かどうか・どう処理するか）は p12 + p18（+ Rs）が持ち、私は判定しません。**

---

## Finding A — 実在（中）: `ROOT_REQUIRED_FIELDS` の drift を、既存のテストは弁別できない

**現状は正常です。** `contracts.py`（`be24c30e…`）の `SkillLifecycleContract` フィールド（`:482-500`）と `ROOT_REQUIRED_FIELDS`（`:511-533`）は、**今日時点で 19 件・名前も完全一致**。

- 機械照合（module は実行せず、テキスト抽出のみ）: 両側 19 件、`comm -3` の差分 **0 行**。

**穴は「一致していること」を守る検査が無いことです。**

- `test_contracts.py`（`58641a87…`）`:18-20` = **件数のみ**（`len == 19`）＋ 1 個の所属確認。
- `test_harness.py`（`e2612076…`）`:107-115` = `good` / `missing` / `unknown` の 3 payload を**すべて `C.ROOT_REQUIRED_FIELDS` 自身から生成**（`:108` / `:110` / `:113`）。
  - ⚠ この test 自体は名前どおりの仕事（`parse_root_fields` の missing/unknown 判定）を正しくしています。**欠けているのは別の結合**です。

**帰結**: dataclass 側でフィールドを**改名**した場合 — 件数は 19 のままなので `:18-20` は PASS、payload は定数から生成されるので `:107-115` も PASS。しかし `harness.parse_root_fields`（`78015cab…` `:120-136`）は**その定数**で manifest の欠落／未知フィールドを弾いているため、**弾く基準だけが実体からズレます**（drift は静かに通る）。

**失敗の型**: 検証集合を、検証対象自身から作っている（本 project で記録済みの型）。

**弁別できる検査（⛔ 未適用・条件④）**: `ROOT_REQUIRED_FIELDS == {f.name for f in dataclasses.fields(SkillLifecycleContract)}` の 1 行。

⭐ 参考: 同じ `harness.py` の別箇所は**この基準を満たしています** — `validate_manifest` は skill_id を件数でなく**集合等値**で検査（`:214-217`）。A は、その水準がここだけ適用されていない、という形の指摘です。

## Finding B — 候補（未確認）: `is_hex64` が末尾改行を通す可能性

- `contracts.py`（`be24c30e…`）`:21` = `re.compile(r"^[0-9a-f]{64}$")`、`:24-26` が `.match()` で判定。
- Python の `re` では `$` が**文字列末尾の改行の直前でも一致する**ため、`"a"*64 + "\n"` が通る見込みです。

**影響範囲（実測 = grep）: 12 箇所が本関数を通ります。**

- `contracts.py` の `__post_init__` 9 箇所: `:196` / `:200` / `:215` / `:242` / `:256` / `:271` / `:298` / `:327` / `:391`
- `harness.py`（`78015cab…`）の manifest 検査 3 箇所: `:236` / `:242` / `:249`

**既存テストは検出できません**: `test_contracts.py`（`58641a87…`）`:23-26` は「正常 / 短すぎ / 大文字」の 3 例のみで、**末尾改行・長すぎ・空文字を試していません**。

**露出の見積り（低）**: 内部生成の hash は `identity.py`（`ca4aeaba…`）`:63-65` の `hashlib.hexdigest()` 由来で改行を含まず、manifest 側は JSON 由来。危険なのは `sha256sum` の出力やテキストファイルから拾った値を渡す経路です。

⛔ **未確認です。** 根拠は「文書化された `re` の仕様＋静的読解」であって実測ではありません。確認には 1 行の実行が要り、**実行は保留中のため行っていません**。

- 確認方法（⛔ 未実行）: `is_hex64("a"*64 + "\n")` が `True` を返すか。
- 修正方向（⛔ 未適用・条件④ / fix は gate 開放後 p14）: `$` → `\Z`、または `re.fullmatch`。

## 観察 C — 欠陥ではない（命名のみ）

`test_contracts.py`（`58641a87…`）`:125` の `test_belief_ref_tagged_union_both_or_neither_rejects` は、「両方あり」の場合を試していません（当該構造体では単一オブジェクトしか保持できず、構成上不可能なため）。本来の both-or-neither 判定は `harness.parse_belief_value`（`78015cab…` `:139-154`）に在り、**実装は正しい**。テスト名だけが被覆を過大に見せます。

## 疑ったが晴れた点（記録として残す）

`Admissibility`（`contracts.py` `:464-471`）は authority 2 軸を既定 `False` にするだけで、**構築時には強制していません**。`contracts.py` だけを読むと欠陥に見えます。

⇒ **欠陥ではありません。** 強制は `harness.py`（`78015cab…`）側の 3 箇所 — `evaluate_conformance` `:77-80` / `assert_no_authority` `:112-117` / `validate_manifest` `:221-224` — に在り、module docstring `contracts.py:9-12` の役割分担どおりです。**`harness.py` を読むまで判定を保留した項目**として記録します。

## 成立を確認できた点（同じ射程で）

- `harness.evaluate_conformance` は算出した適合性と**申告値の一致**を要求（`:103-108`）⇒ `contract_conformant` が言い張りの定数にならない。
- `validate_manifest` は skill_id を**集合等値**で検査（`:214-217`）。
- `verify_manifest_artifacts` は manifest の hash を**実ファイルの digest と照合**し、ファイル不在の行を**明示的に skip**（`:256-295`）⇒ 証拠不在を黙って PASS にしない。

## ⛔ 本書で行っていないこと

- **実行**（対象 module の実行・テスト再実行）— していません。
- **修正** — していません（条件④ / fix は gate 開放後に p14）。
- **LEDGER / status / planning 面への反映** — していません（条件③）。
- **判定** — していません（条件① / 「反証した」項目は 0 件）。

---

起草 = w2:p15（IMPL-VERIFIER2）。disposition = p12（p18 経由 relay `-212`、2026-07-27 18:22 JST）。読解 = 2026-07-27 14:0x–14:2x JST / 版の固定 = 2026-07-27 18:23:15 JST。
