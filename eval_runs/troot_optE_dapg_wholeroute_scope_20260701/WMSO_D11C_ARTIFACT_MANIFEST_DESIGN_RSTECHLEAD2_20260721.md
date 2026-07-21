# WMSO D1.1-C `artifact_manifest` — DESIGN **v2.5（縮小版・fixture 同梱）**

- node `T-WMSO` D1.1-C／著者 = `w2:pQ` RS-TECH-LEAD2／作成 = **2026-07-21 15:5x JST**（shell 実測）
- 系譜: **v1**（`726f684c52421928…` @ `33e67626da`）= debate cycle-1 **FAIL**（`9851f165a5fc45eb…` @ `7f6d038a30`・ACCEPT 24）→ **v2 / v2.1**（`f0ffe2e016d7302f…` @ `5e82a3326d`）= debate cycle-2 **FAIL**（`df2965a8e0d2927e…` @ `78d02f4257`・ACCEPT 16 群）→ **本 v2.2**
- **縮小の基準** = Rs 逐語「確かな前提条件があるほうを選べ」／custody = `WMSO_RS_D11C_REDUCTION_CRITERION_CUSTODY_20260721.md`（`90f7f1e6dceb835c…` @ `57d4dbb59c`）。⚠**同 custody §4 のとおり、承認済 scope を縮めてよいか自体は Rs 未裁定（open-11）**
- **scope の正** = prereg（`d9caaffcf29d9524…` @ `1860edcc1c`）§2 IN / §3 OUT
- 土台（凍結・編集しない・**4 file**）: contracts_v2 `00192d20ca00b654…`／EP md `c474acea7c58acc2…`／EP JSON `e63176af9bc3a246…`／tensor_binding v13 `5a1874d3be8b98b8…`
- ⛔**impl / training / closed-loop authority / push / freeze / slice = CLOSED 継続**

## 0. 本版の範囲

⚠**v2.1 の「凍結が名指しで委任したのは 2 件のみ」は誤りだった（cycle-2 F-1）**。凍結が D1.1-C を名指しする委任は**もっと多い**。実測で確認できた範囲:

| 委任 | 委任元 | 本版 |
|---|---|---|
| **U-5 両段 binding 記録** | 凍結 v13 `:169` / `:378`／DDR **#29**（owner pQ/p5） | ⭐**設計する** |
| **`substrate_id`** | 凍結 contracts_v2 `:570` carry (i)／v13 `:376` | ⭐**設計する** |
| **U-2 producer artifact pin** | 凍結 v13 `:375`／DDR **#28** 逐語「D1.1-C prereg … owner **pQ — C prereg で解決**」 | ⛔**本版では設計しない**（open-1） |
| **U-6 topology metadata** | 凍結 v13 `:380`／DDR **#30** 逐語「D1.1-C prereg + 契約層閉鎖 … **pQ/Rs**」 | ⛔**本版では設計しない**（open-1） |
| **package 全体への JCS 展開** | 凍結 v13 `:24` = prereg IN-4 | ⛔**本版では設計しない**（open-2） |
| **版 bump 移行手続** | 凍結 v13 `:185` | ⛔**設計しない・prereg IN に無い**（open-3） |
| **宣言↔producer code の責任 owner** | 凍結 v13 `:392`（venue = 「impl 解錠時 **or** D1.1-C prereg」） | ⛔**owner ゼロ**・impl は CLOSED（open-13） |
| **実 binding の代表性** | 凍結 v13 `:365`「実 binding の代表性は D1.1-C の run manifest が担う」 | ⛔**設計しない**（open-13） |
| **訓練時実次元 pin の非拘束推奨** | 凍結 v13 `:211` | ⛔**設計しない**（open-13） |
| **v1 harness の後継**（`validate_manifest` 等・`d1_exit` HOLD guard） | 凍結 contracts_v2 `:437`「D1.1-C 後継まで」 | ⛔**設計しない**（open-13）・⭐**open-5 の retire 点を凍結が既に定めている** |

⛔**本版が設計しないもの（完全列挙）**: prereg §2 **IN-1（manifest 型の全体）／IN-3（grade 別 proof obligation の供給写像）／IN-4（JCS package 展開・CI）／IN-5 のうち U-2・U-6**。
⇒ ⭐**本版で D1.1-C は閉じない**。
⚠⚠**cycle-3 G-5**: **IN-2 も部分履行**である。prereg IN-2 逐語は「異なる substrate の silent pooling を**禁止**する（検出・拒否の code を含む）」だが、§3 は「黙って混ざらない」の保証を**撤回**した（open-9）。⇒ 「設計する 2 件」は正確には **1 件 + 部分 1 件**。⚠ なお**承認済 prereg 自身も §3 OUT-1 で substrate policy を DDR #26 に帰属**させており（§3 と同じ誤同定）、これも未 surface だった（open-14）。

**選抜の基準（前提の確かさ）**: 設計する 2 件の前提は**凍結の逐語のみ**で、いずれも実測済み・**未裁定の policy に非依存**。設計しない項目は §8 の未決（repo 内の別 canonicalization ／ Rs 判断 (a)(b)(c) ／ 前提訂正後の供給写像の再導出 ／ 版 bump の scope 欠落）に乗る。
⚠**過小履行も scope 逸脱である**（cycle-2 F-10）⇒ **縮小の可否は Rs 判断 (c)＝open-11**。

## 1. v1 の中心前提は **FALSE**（訂正記録）

- **誤っていた主張（v1 §3 open-1）**: 「required set は exact ゆえ HB 以下は `TRAIN_RUN_MANIFEST` を追加携行できない ⇒ manifest は EXACT 経由でしか到達しない」。
- **正しい読み**: `E_PROOF_KIND_FOREIGN` は **component 意味論**（凍結 EP md `:114`「component に意味を持たない kind の混入」／`:129(iii)` 例示「POLICY_ARTIFACT claim に INPUT_SCHEMA_HASH」）。`TRAIN_RUN_MANIFEST` は **EXACT 13/13 cell で required**（pQ 実測）⇒ 非 foreign。
- ⭐**決定脚（pS 提示・pQ が閉じた列挙で再測・cycle-2 で 4 file へ拡張）**: 凍結に **set-equality / 超過拒否の規則が無い**。**凍結 4 file** の proof 系 error 語彙 = `ARTIFACT_UNRESOLVED` / `CONFLICT` / `INSUFFICIENT` / `KIND_FOREIGN` / `MISBOUND` / `PAYLOAD_MISSING` / `REF_MALFORMED` のみで、**非 foreign な余分を拒否する code は 0 件**。`superset` / `excess` / `extraneous` = **4 file とも 0 hit**。⚠**誠実な範囲 = error code 語彙上の不在**（散文規則の不在は主張しない）。
- **誤りの型**: 「**required SET が厳密（spec の性質）**」を「**record が超過携行不可（instance の禁止）**」に取り違えた。
- ⭐**携行可 ≠ EXACT 達成**（grade は測定値・凍結 `E_GRADE_MISMATCH`）。
- **機序（自己記録）**: 凍結 EP の **JSON の 1 文字列**だけを読み、**自分が土台に挙げた EP markdown を開かなかった**。

### 1.1 ⛔ 凍結文書への波及 — **事実のみ**（判定は Rs）

⚠**cycle-2 F-9 の訂正**: v2.1 はここで「限局している」「load-bearing でない」と**私が判定していた**。誤前提を出した側にその誤りが immaterial だと決める standing は無い。**以下は実測事実のみを置き、推論は Rs へ渡す。**

- 凍結 v13 **`:256`**（D-1..D-4 選定表・`B1D-A`）逐語「`proof_policy._domain` = 「exact required ProofKind set」＋ `E_PROOF_KIND_FOREIGN`」。同行に「**D-3 に合流**」も在る。
- 凍結 v13 **`:471`** は同旨の再掲だが、集合の呼び方が「exact **required ProofKind** set」ではなく「**exact set**」と縮約されている（⚠ v2.2 は「「kind」の語を含まない」と書いたが `E_PROOF_KIND_FOREIGN` は同行に在り**逐語で偽**だった＝ cycle-3 G-13）。
- 凍結 v13 **`:252`**（D-1 の採択理由）= 「frozen delta 不要／1 hop／B 側宣言 1 個／contracts_v2 `:396` の provenance 意味論適合」— **proof kind 集合への言及なし**。
- 凍結 v13 **`:258-262`**（D-1 の反証条件 4 件）= `source_ref` 意味論／registry 衝突／resolver 到達性／1 hop — **proof kind 集合への言及なし**。
- 当該 arc は B1 = D-1 採択に接続し、**Rs ratify 2026-07-20 21:44** が乗っている。
- ⛔**Rs 判断**: **(a)** 凍結 v13 `:256`/`:471` の併記訂正（**凍結編集 = Rs 専権**）／**(b)** 採択 D-1 への影響の正式判断。
- 記録: pY custody `b602a8c8030d47a7…` @ `337d08d787`／pS consult `b4ec93173db6c24c…` @ `a31adca295`。

## 2. U-5 — 両段 binding の記録機構

```python
class StageBindingRecord:                        # 注: 型注釈は PEP-604 を用いない（3.8 床）
    execution_stage_tensor_binding_hash          # 64-hex or None
    bc_stage_tensor_binding_hash                 # 64-hex or None
```

- 命名 = 凍結の claim target（EP JSON `:29` `execution_bundle.tensor_binding.artifact_hash`）に合わせる。
- **lineage 別の全域表**（凍結 `TrainingLineage` 5 member を全被覆）:

| lineage | execution 段 | bc 段 | 違反 |
|---|---|---|---|
| `NOT_APPLICABLE` | **null でも 64-hex でもよい**（bundle の slot に従う） | null 必須 | bc 非 null = `E_MANIFEST_STAGE_BINDING_PRESENT` |
| `RL_ONLY` | 64-hex 必須 | null 必須 | 欠落 = `…_MISSING`／bc 非 null = `…_PRESENT` |
| `BC_ONLY` / `BC_THEN_RL` / `DEMO_PLUS_RL` | 64-hex 必須 | 64-hex 必須 | 欠落 = `…_MISSING` |

⚠**cycle-2 F-8 の訂正**: v2.1 は `NOT_APPLICABLE` で execution 段も null 必須としていたが、**凍結 v13 `:166` が null を要求するのは bc 段のみ**であり、SCRIPTED/WAIT が KNOWN な `tensor_binding` slot を持つ構成は契約上正当（EP JSON `:29`）。旧規則は**正直な記録を false-reject** していた。

- **凍結 declaration との突合**（凍結 v13 `:158-166`）:
  - ⭐**lineage 整合（cycle-2 F-6 で追加）**: 記録の `training_lineage` == 凍結 `LineageBindingDeclaration.training_lineage`。不一致 = **凍結 `E_BINDING_LINEAGE_MISMATCH` を再利用**（v13 `:230`・新 code を作らない）。⚠⚠**cycle-3 G-6 の宣言**: 凍結 `:171` は同 code を **`TrainingProvenance.training_lineage` との比較**に定義し、`:230` は **certify 時**の cross-artifact 検査に置いている。本版は **別 operand（`LineageBindingDeclaration`）・別発火点（C 側 record 検査）**で用いる ⇒ **凍結 code の適用域を広げている**。「新 code を作らない」を満たす代わりに凍結の意味に触れる決定であり、**Rs 判断へ回す**（open-15）。⚠ これが無いと **DEMO_PLUS_RL の run が `NOT_APPLICABLE` を名乗って両段 null で通り、U-5 が 0 code で破られる**（cycle-2 実証）。
  - `relation == IDENTICAL` ⇒ 両 field 非 null かつ相等。
  - `relation == EXPLICIT_SUPERSEDE` ⇒ bc 段 == 凍結 `TensorBindingSpec.lineage_declaration.bc_stage_binding.demo_dataset_binding_hash`（⚠ **dataset の content hash とは別物**・v2.1 の短縮 path 表記は凍結に存在しなかった＝ cycle-2 F-16 訂正）。
  - 不一致 = `E_MANIFEST_STAGE_BINDING_CONFLICT`。
- ⛔**「解消する」とは書かない**: 凍結 `E_BINDING_STAGE_IDENTICAL_UNCONFIRMED` は certify 時の cross-artifact 検査（v13 `:230`）で、凍結 `certify_inputs`（EP JSON `:149`）に manifest は入らない。**本版が与えるのは記録であって discharge ではない**（open-4）。

## 3. `substrate_id` — 必須化と区別機構

```python
substrate_id                 # str（本記録が pin する run の substrate）
dataset_substrate_ids        # str の列（bytes 昇順・重複禁止）
```

| # | 述語 | 違反 code |
|---|---|---|
| S-1 | `substrate_id` が存在し非空 | `E_MANIFEST_SUBSTRATE_ABSENT` |
| S-2 | 構文適合（ASCII・`[A-Za-z0-9_.:-]{1,64}`） | `E_MANIFEST_SUBSTRATE_MALFORMED` |
| S-3 | `dataset_substrate_ids` が **非空**かつ **bytes 昇順・重複なし** | `E_MANIFEST_SUBSTRATE_POOLED` |

- ⛔⛔**値では弾かない**: 述語は **存在・構文・相互比較**の 3 種のみ。allowlist も denylist も grade 係数も持たない。
- **凍結 carry の全文**（cycle-2 F-14 = v2.1 は第 1 連言を落として引用していた）: contracts_v2 `:570` (i) 逐語「**D2 transition data = 修正済み clean substrate のみ**・旧 contaminated log は明示 **substrate_id** を付け silent pooling 禁止」。⇒ **2 連言**であり、本機構が担うのは**第 2 連言（記名の強制）のみ**。第 1 連言（clean のみ）は**選別 policy** ゆえ本設計は述べない。
- ⚠⚠**保証の範囲（cycle-2 F-14 の訂正）**: 保証するのは **「記名されていること」と「記名された集合が正規形であること」のみ**。⛔**「黙って混ざらない」は保証しない** — 列挙漏れは記録単体から判定できない（open-9）。v2.1 の保証文は撤回する。
- ⚠**cycle-2 F-11 の訂正**: v2.1 は混成の可否を「**DDR #26 の裁定**」としていたが、LEDGER の #26 は「**P0 substrate defect（隠れ綱引き）の banked-evidence 影響**」であり**混成 policy の裁定ではない**（pQ 実測）。⇒ **混成可否を裁定する DDR は現存しない**。本設計は可否を述べず、**裁定者の不在を open-8 として上程**する。
- ⚠**MIXED は導出値であって field ではない**（v2.1 は「MIXED として記録する」と書いたが記録 field が無かった）。`len(dataset_substrate_ids) >= 2` から導出できる、と述べるに留める。

## 4. 直列化と hash

- **凍結 §2 WCJ を適用**（新 canonicalization を作らない）＋ 凍結 v13 `:24` の B-declared 3 規約を継承。
- ⚠⚠**cycle-2 F-13 の訂正 — 直列化器は並べ替えない**: v2.1 は「集合として正規化」と書いたが、**実装も凍結規約も array を並べ替えない**（凍結 **contracts_v2** `:178` の bytes 昇順は **frozenset** 型の規則で、本 field は列。⚠ v2.2 は host を落としており、直前の引用が v13 だったため **v13:178 と誤読され得た**＝ cycle-3 G-13）。本版は **順序を検証（拒否）で担保**する。⇒ ⚠**validate を通さずに hash する producer は同じ集合から別の byte 列を出せる**（open-10）。
- **時刻を hash preimage に入れない**。⚠ v2.1 は「付随 metadata に置く」と書いたが**その置き場が存在しなかった**（cycle-2 F-16）⇒ **本版は時刻を記録しない**。
- **配布 bytes は canonical bytes と byte 一致であること**（`E_MANIFEST_NONCANONICAL_BYTES`）。⚠**検出であって阻止ではない**。実行箇所 = §7 の `--verify`（**parse → 再正規化 → byte 比較**。v2.1 は parse せず file 内定数と比較するだけで**自己証明**だった = cycle-2 F-3）。

## 5. error code = **8 件**（C 側）

拒否規則 6: `E_MANIFEST_SUBSTRATE_ABSENT` / `…_MALFORMED` / `…_POOLED` / `E_MANIFEST_STAGE_BINDING_MISSING` / `…_PRESENT` / `…_CONFLICT`
＋ **`E_RECORD_SHAPE`**（key 集合・型・enum member・64-hex の shape 違反。⚠ v2.1 は「decoder ゆえ code でない」と処理していたが**実装が code として発している** = cycle-2 F-12）
＋ builder 側 1: `E_MANIFEST_NONCANONICAL_BYTES`

- **再利用（新設しない）**: lineage 不整合 = 凍結 `E_BINDING_LINEAGE_MISMATCH`（⚠ 適用域拡張 = §2 の G-6 宣言）。⚠⚠**`E_PROOF_ARTIFACT_UNRESOLVED` の記載は撤回**（cycle-3 G-13）: 本版の記録には解決すべき artifact 参照 field が無く、**実装も control も存在しない** ⇒ **宣言のみの到達不能 code** だった。後続版が artifact 参照を持ったときに再掲する。
- ProofKind enum の出典 = **contracts_v2 `:236-240`**。

## 6. Reuse gate（AGENTS.md「Reuse / official-specification gate」）— repo に対して実行

- ⭐⭐**cycle-3 G-4 で読みが変わった — 「未決」ではなく「非適合」の可能性が高い**: 凍結 **contracts_v2 `:168`** が key 順を逐語で決めている（「object key sort = UTF-16 code unit 順（`k.encode("utf-16-be")` bytes 昇順）」）。⇒ 下記 2 site は**凍結規則に非適合**であり、対等な候補ではない。さらに **D1.1-B fixture の `wcj_bytes` も同じ挙動**＝ **凍結 chunk 内の非適合**（§1.1 と同型の凍結波及・未上程だった）。⇒ 実態は「3 実装が併存」ではなく「**2 挙動 / 3 site で、凍結に適合しているのは本版のみ**」。⚠ 現行 corpus は全 ASCII ゆえ差は **latent**。
- **旧記述（open-5）**: `thread_isaac_lab/wmso/d1/identity.py:80-82` の `canonical_json()` = `json.dumps(sort_keys=True, ensure_ascii=False, separators=(",",":"))` は **凍結 WCJ と別物**。⭐**本版の encoder vector がこれを判別する**（§7）: 同一入力に対し WCJ = `{"😀":2,"！":1}` ／ `sort_keys=True` = `{"！":1,"😀":2}`（pQ 実測）。⇒ **どちらが正かは本版では決めない**（owner を付けることが freeze の前提 = open-5）。
- ⚠ 同 node には D1.1-B fixture の `wcj_bytes` も在り、**正規化の実装は 3 つ**（cycle-2 F-16）。
- ⛔⛔**引用面の注意（cycle-2 F-7）**: `./isaaclab.sh -p` が非零 exit を隠す旨を記す **AGENTS.md の当該記述は、本 pin 時点で commit されていない**（`git show HEAD:AGENTS.md` に 0 hit／working tree に 1 hit／`git status` = ` M AGENTS.md`・pQ 実測）。⇒ **本 doc は当該記述を「on-disk as-read」としてのみ引用**し、committed 典拠としては引かない。⚠**本 session で 3 度目の同型**（`CLAUDE.md` 未 commit 統治 = DDR #35 と同族）⇒ **open-7 として面へ surface する**。

## 7. Fixtures / test（**bank 済 — 宣言でなく実物**）

**banked**（`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/wmso_d11c_fixtures/` @ `e1ed170014`）:

| file | 内容 | sha256（先頭 16） | bytes |
|---|---|---|---|
| `carry_record_golden_A.json` | `NOT_APPLICABLE`（両段 null） | `ce474f3ad393767a` | 224 |
| `carry_record_golden_B.json` | `DEMO_PLUS_RL` × `IDENTICAL`（両段一致・substrate 2 値） | `f49d15698bf379c1` | 376 |
| `carry_record_golden_C.json` | `BC_THEN_RL` × `EXPLICIT_SUPERSEDE`（**bc ≠ execution**） | `1b88fdc0c95813de` | 350 |
| `carry_record_golden_D.json` | `RL_ONLY`（bc = null） | `4971d3f7a6601ff3` | 285 |
| `build_goldens.py` | 生成器 + 非破壊 `--verify`（v2.3: **pin 済 digest を外部アンカーとして照合**・`__pycache__` の偽 FAIL を除去）（stdlib のみ・PEP-604 不使用ゆえ 3.8 で parse 可。⚠**3.8 実機は本 host に無く未実測**） | `1c4eebff59c520c8` | 22965 |

- **control = 33 本**（拒否 15・declaration 3・golden の positive 4・**encoder vector 5**・encoder reject 5・**非 canonical bytes 1**）。**期待 code は完全一致で判定**（v2.1 は部分一致だった = cycle-2 F-16）。
- ⭐**encoder vector が判別する（cycle-2 F-2 の中核修正）**: 期待バイト列を**手で導出**して埋め込む（この encoder で生成しないので自己循環しない）。U+FF01 は UTF-16-BE で `FF 01`・UTF-8 で `EF BC 81`、U+1F600 は UTF-16-BE で `D8 3D DE 00`・UTF-8 で `F0 9F 98 80` ⇒ **両者の順序が逆転する**。実測: WCJ = `{"😀":2,"！":1}` ／ `sort_keys=True` = `{"！":1,"😀":2}` ／ 無 sort = 同左 ⇒ **3 実装すべて不一致で落ちる**。v2.1 の golden は全 ASCII で**どの実装でも byte 同一**だった。
- ⭐**`--verify` は parse する**: bytes → `json.loads` → **再正規化して byte 比較** → `validate` → 期待 record と一致。さらに **fixture dir の予期しない entry を拒否**（`__pycache__` を実際に検出した）。
- ⛔**argv guard（cycle-2 F-4）**: subcommand は `--verify <dir>` / `--emit <dir>` のみ。**引数落ち・flag 落ちは rc=2 で何も書かない**（実測）。v2.1 は `--verify` 単独で `--verify` という名の dir を作って書き込み rc=0、`<dir>` 単独で **banked golden を上書き**していた。
- ⛔**fail-closed 実行コマンド（事前登録・C 側で実測）**:
  ```
  /home/rlrk/IsaacLab/env_isaaclab/bin/python /home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/wmso_d11c_fixtures/build_goldens.py \
      --verify /home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/wmso_d11c_fixtures
  ```
  **実測**（非 canonical bytes を注入し、**sha が `ce474f3ad393767a` → `555ffe870dc6e899` に実際に変化したことを確認してから**測定）:

  | 呼び方 | rc |
  |---|---|
  | `python3` / `/usr/bin/python3` / `/home/rlrk/env_isaaclab/bin/python` / `/home/rlrk/env_isaaclab7/bin/python`（**絶対 path**） | **1** |
  | `./isaaclab.sh -p` | ⛔**0（fail-open）** |

  ⚠**v2.1 の表は `env_isaaclab7/bin/python` を相対 path で書いており、repo 直下からは rc=127**（cycle-2 F-16）⇒ 絶対 path に訂正。復元後 sha 一致・clean rc=0・4/4 PASS・33/33 fired を実測。
- ⛔**builder が検査しないもの（cycle-3 の mutation 研究 40 件で実測・G-7/G-13）**: JCS escape の全域／duplicate key（Python dict で表現不能）／非 BMP key の全域／⚠**`--verify` の on-disk leg のうち byte 比較以外（予期しない entry・欠落 file・期待 record 比較・失敗の伝播）に control が無い**（単点欠陥 5 件が 33/33 のまま生存）／⚠**argv guard に control が無い**／⚠**`emit()` が非原子**（不適合 golden の直前まで上書きしてから拒否）／⚠**`33` は assert されない**（`fired == total` を検査していない）／⚠**encoder の reject は値側のみで key 側は未検査**（lone surrogate key は `UnicodeEncodeError` で落ちるが `WcjError` ではない）。**WCJ 完全性は impl の `canonicalize()` leg**。
- ⚠**代表性を主張しない**（合成物・型網羅が目的）。

## 8. Open points（⛔`open = 0` を宣言しない）

1. ⛔**U-2（DDR #28）／U-6（DDR #30）を本版で設計していない** — 両者とも凍結が D1.1-C を名指しし、DDR の owner は **pQ**（#30 は pQ/Rs）。後続版で設計する。
2. **IN-4（JCS package 展開・CI）未着手** — 凍結 v13 `:24` の名指し委任。DDR #35（`validate.sh` の偽 FAIL）と接する。
3. **凍結 v13 `:185` の版 bump 移行手続**が承認済 prereg §2 IN に無い ⇒ **IN 集合が既知の不完全**。scope 裁定 = **Rs**。
4. **U-5 は記録であって discharge でない**（§2）。
5. **`identity.py:80-82` との正規化衝突に owner が無い**（§6）。⇒ **freeze の前提**。
6. ⛔**Rs 判断 (a)(b)**（§1.1）。
7. **`AGENTS.md` の当該記述が未 commit**（§6）— repo 全体の統治事項として surface する。
8. **混成 substrate の可否を裁定する DDR が現存しない**（§3）。
9. **`dataset_substrate_ids` の網羅性は記録単体から判定不能**（producer の義務）。
10. **直列化器は並べ替えない** ⇒ validate を通さない producer は同一集合から別 byte 列を出せる（§4）。
11. ⛔**Rs 判断 (c) = 承認済 scope（IN 5 項）を 2 項へ縮小してよいか**（cycle-2 F-10・custody §4）。
12. **prereg §4 carry の残り**: ②#28 ④#30 は open-1 に、③**#29 = demo 再記録**（198 demo）⑤**#31 = trainer 実在**は本項に保持。⇒ **`portfolio_has_IL` は本 chunk 完了だけでは true にならない**。⚠ carry ①#26（選別 policy 非焼込）は §3 で恒久遵守中（討議で数え落としていた）。
13. **凍結の名指し委任 4 件を本版が扱っていない**（§0 追加分）: v13 `:392`（**owner ゼロ**）／`:365`／`:211`／contracts_v2 `:437`。**owner = Rs（`:392` の venue 指名）／後続版（他 3 件）**。
14. **承認済 prereg §3 OUT-1 も DDR #26 を誤同定している**（§0）。**owner = Rs / pS**。
15. **凍結 `E_BINDING_LINEAGE_MISMATCH` の適用域拡張**（§2 の G-6 宣言）。**owner = Rs**。
16. **v2.1 で無処置に消えた open 2 件を復活**（cycle-3 G-13）: ①**run をまたぐ pooling を宿す object が承認済 scope に無い** ②**`IDENTICAL` の等値検査は execution 段 hash の複写でも通る**（cycle-1 A-7 の捏造経路。⚠ 凍結が委任したのは「両段に同一 hash を記録していることの照合」ゆえ、解決可能性の要求は**凍結を超える強化**＝上程事項）。**owner = pS / Rs**。
17. **pS / pY の受諾済 carry を本文に明記していなかった**（cycle-3 G-9）: **P-1** =「**code = error-code / 拒否規則の *設計*・package / CI = 構造と check の *仕様*（build でない）**」⇒ 本版は 21KB の実行可能 builder を bank しているため**特に明記が要る**（bank 自体は D1.1-B 先例あり）／**W-2** = U-6 の delta-free 確認（U-6 は本版の外＝open-1）／**pY note-2** = IN-3 は obligation の設計であって proof 生成ではない（IN-3 は本版の外）。
18. **本 design が引く Rs 逐語は CC1 の transcription**（custody §5）。**byte 忠実性は独立検証されていない**／**Rs 拒否権は残る**（approval custody §4）。⇒ 本版の authoring 自体が未承認扱いに戻り得る。

## 9. 版歴

- **v2.4**（本版・18:0x）= cycle-3 の doc 側 G-3〜G-13 を fold。§0 に**未扱いの凍結委任 4 件**と **IN-2 部分履行**を追記／§1.1 の `:471` 逐語を訂正（v2.2 の記述は**逐語で偽**だった）／§2 で**凍結 code の適用域拡張を宣言**し Rs へ／§4 の `:178` に host を復元／§5 で **`E_PROOF_ARTIFACT_UNRESOLVED` の記載を撤回**（到達不能）／§6 で **open-5 を「未決」から「非適合の是正」へ読み直し**（D1.1-B fixture の非適合も明記）／§7 の「検査しないもの」を **mutation 研究の実測**で拡張・登録コマンドを絶対 path 化／§8 を **18 件**にし owner を付与。⚠**Rs 判断 (c) の framing 訂正は routing `e699aa86ac02e001…` @ `1c77a24430` 側で実施済**（「scope 縮小の可否」→「部分版 two-key の可否 / open-freeze の可否」）。

- **v2.3**（15:5x 追補）= cycle-3 の計器 2 件を修正。①**登録済コマンドが `__pycache__` で rc=1 になる偽 FAIL**（`sys.dont_write_bytecode` は import 経路では無効 = DDR #35 と同型）⇒ 許可 entry に追加。②**協調改竄が rc=0 で通る**（builder 内定数だけが oracle だった）⇒ **golden 4 本の pin 済 digest を builder に埋め込んで照合**。実測: `__pycache__` 有りで rc=0 / 33/33 / 4/4、協調改竄で rc=1、非 canonical control も発火。⚠ **cycle-3 の残り（doc 側 G-3〜G-13）は未 fold**。

- **v2.2**（本版・15:5x）= cycle-2 の 16 群を fold。**§0 の委任集合を訂正**（U-2/U-6 を非設計として明示）／**§1.1 から私の immateriality 判定を削除**（事実のみ）／**§2 に lineage 整合を追加・`NOT_APPLICABLE` の false-reject を除去**／**§3 の保証文を縮小・`:570` を全文引用・DDR #26 の誤同定を訂正**／**§4 の「正規化」を「拒否で担保」に訂正**／**§5 を 8 件に**／**§6 で AGENTS.md 未 commit を明示**／**§7 = 判別する encoder vector・parse する verify・argv guard・33 control・絶対 path の rc 表**／**open を 12 件に**。
- **v2 / v2.1**（15:1x–15:2x・`f0ffe2e016d7302f…` @ `5e82a3326d`）= 縮小 + cycle-1 fold + fixture 初版。**cycle-2 FAIL**。
- **v1**（14:2x・`726f684c52421928…` @ `33e67626da`）= 初版。**cycle-1 FAIL**。
