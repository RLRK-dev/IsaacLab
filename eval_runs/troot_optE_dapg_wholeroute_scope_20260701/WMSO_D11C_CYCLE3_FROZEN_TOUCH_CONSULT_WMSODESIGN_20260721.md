# WMSO D1.1-C cycle-3 凍結波及 2 件 — 設計軸 照会回答（pS MWSO-DESIGN）

- node: `T-WMSO` D1.1-C; 検証者 = `w2:pS` MWSO-DESIGN（0-commit）。作成 = 2026-07-21 18:31 JST（shell 実測）。
- **照会** = pQ 18:23（Rs 承認済・⛔**two-key の key 依頼でない**・部分版 freeze の可否は Rs 判断 (c) として未裁定・順序を逆にしない）: cycle-3 で凍結に触れる所見 2 件（G-4 canonicalization / G-6 error code 再利用）の設計軸の読みを Rs 裁定材料として。
- **対象 pin（on-disk 自算・一致）**: design v2.4 = `b85fa905d4a60299ba751061d1e1bcf59a4e1bfbaebe4c4e27642b021a580fa4` @ `c0baa08663` / cycle-3 verdict = `d23e5faaa8d612735b6014914bdb1ab3a9917ebec24cf2911a5c73304222bdaf` @ `acce4d5c79` / routing = `e699aa86ac02e0018bfad816cb8681ad6284e4a9d4e2d3ea848a63ae18d20def` @ `1c77a24430`。凍結 4 file は `1860edcc1c` で読了。
- ⛔**設計軸のみ**。⛔**凍結 file は編集しない**。⛔**key を開かない・disposition は Rs**。

## 1. G-4（canonicalization: UTF-16 vs codepoint）— open-5 は「是正」（「未決」でない）

**凍結が逐語で決めている（私が自読）:**
- 凍結 contracts_v2 `:168` 逐語「object key sort = **UTF-16 code unit 順**（`k.encode("utf-16-be")` bytes 昇順）」。`:171-172` = 2 層（raw-WCJ = full-Unicode key / typed 入口 = ASCII-assert）・**golden vectors は「非 BMP key」を必須**。⇒ **凍結 spec は UTF-16 を規範として確定している**（RFC 8785）。

**3 site / 2 挙動（私が各 file を自読）:**
| site | 実体 | 適合 |
|---|---|---|
| identity.py `:80-82` | `json.dumps(sort_keys=True, ensure_ascii=False)` = **codepoint 順** | ⛔非適合（**impl・custody-closed でない**） |
| D1.1-B fixture `build_goldens.py:208` | 同 `sort_keys=True` = **codepoint 順** | ⛔非適合（**custody-closed D1.1-B 内**） |
| D1.1-C fixture `build_goldens.py:95` | `kv[0].encode("utf-16-be")` | ✅**適合**（`:119` に非 BMP 判別 vector `{"！":1,"😀":2}`） |

⇒ **① open-5 = 「非適合の是正」で正しい**（「どちらが正か未決」でない）。凍結 `:168` が UTF-16 を規範に確定しているため codepoint 順の 2 site は非適合であり対等な候補でない。C の設計（D1.1-C fixture `:95`）は**唯一の適合 site**で、encoder vector が非適合を判別する ⇒ **C は誤りを伝播せず、むしろ検出側**。pQ の v2.4:118 の読み直しは正しい。

**⭐② D1.1-B fixture = 第 2 の凍結 locus だが「値の誤り」でなく「方式の latent 非適合」（重要な区別・disposition を変える）:**
- D1.1-B の golden **key** は全て ASCII/BMP（grep 確認: 非 BMP key `\U0001…` 0 件・唯一の非 ASCII key `:355` は BMP `U+0301` で codepoint=UTF-16）。**UTF-16 と codepoint は非 BMP でのみ分岐**するため、D1.1-B の**banked hash 値は正しい**（coincidence）。
- 非適合は**導出方式**（`:208` sort_keys=True）に限局。**誤った hash は banked されていない** — 非 BMP key が入った場合にのみ誤値を生む landmine。
- ⇒ これは custody-closed chunk 内の**方式 conformance の是正**であり、**値完全性の緊急事態ではない**。

**locus 別 disposition（私は編集しない・Rs 材料）:**
- 凍結**規範 spec**（contracts_v2 `:168`）= **正しい**（欠陥なし）。
- **identity.py**（impl・CLOSED・custody-closed でない）= 適合する comparator で build すべき（D1.1-C fixture `:95` が既に実装）・非適合 canonical_json を wire しない。**frozen 編集でなく impl 義務**（reuse-first ≠ 非適合 impl の再利用・cycle-1 A-13 と同旨）。
- **D1.1-B fixture** `:208`（custody-closed）= 方式訂正 = **凍結編集 = Rs**（値は正しいゆえ低緊急・latent）。
- ⇒ open-5 owner: C の設計は既に適合（`:95`）。open 実体 = (i) D1.1-B fixture 方式（Rs・latent・値正）(ii) identity.py impl（build-conformant・CLOSED）。

## 2. G-6（`E_BINDING_LINEAGE_MISMATCH` 再利用）— 凍結意味論に触れる（Rs）・v13:169 委任の内側でない

**凍結が定めている operand と発火点（私が自読）:**
- 凍結 v13 `:171` 逐語「整合規則: `training_lineage == TrainingProvenance.training_lineage`（`E_BINDING_LINEAGE_MISMATCH`）」= operand は **TrainingProvenance**。`:230` = cross-artifact（**certify 時**・全 operand slot KNOWN 時のみ発火）。
- 凍結 v13 `:169` の外部照合委任 = **「run manifest が両段に同一 `tensor_binding_hash` を記録していること」**で、発火 code は **`E_BINDING_STAGE_IDENTICAL_UNCONFIRMED`**（別 code）。**lineage 検査も `E_BINDING_LINEAGE_MISMATCH` の再利用も委任していない**。

**pQ の再利用（design v2.4 `:75`）:** 記録の `training_lineage` == `LineageBindingDeclaration.training_lineage`・不一致 = `E_BINDING_LINEAGE_MISMATCH`・**C 側 record 検査**。

⇒ **凍結意味論に触れる（Rs）で正しい・v13:169 委任の内側でない**:
- v13:169 の委任は**別 check（tensor_binding_hash 同一性）× 別 code（STAGE_IDENTICAL_UNCONFIRMED）**で narrow。pQ の再利用は**別 operand（LineageBindingDeclaration ≠ TrainingProvenance）× 別発火点（C record 検査 ≠ certify）**ゆえ、この委任には含まれない。
- 凍結 code は defined trigger（operand + 発火点）を持つ契約要素。**別 trigger で同名を再利用 = code の overload**（consumer が `E_BINDING_LINEAGE_MISMATCH` を見ても**どの check が落ちたか判別不能**になる）。⇒ 凍結意味論に触れる = Rs。**pQ の自己 flag（open-15・owner=Rs・design v2.4:171）は正しい disposition**。

**⭐設計軸材料（Rs 判断の助け・私は決めない）:**
- **check 自体は妥当**（design v2.4:75: これが無いと DEMO_PLUS_RL run が NOT_APPLICABLE を名乗り両段 null で通り U-5 が 0 code で破れる — cycle-2 実証）。⇒ 問題は check の要否でなく **code の identity** のみ。
- **reuse-first vs frozen-overload の緊張の解**: reuse-first は**同一 check（同 operand・同発火条件）が再帰する時**に code を再利用する規律であって、**構造的に別の check（別 operand・別発火点）を 1 名に押し込む規律ではない**。⇒ 構造的に別の check には **新 C 側 code（例: manifest-lineage 用）が凍結 overload を避ける clean な解**で、reuse-first に反しない。
- reuse-overload / 新 code / 凍結 code を一般化（両 operand を covering する frozen 編集）の 3 択とも Rs に属す（前 2 者は C の識別選択だが overload は凍結 semantics に触れ、後者は凍結編集）。⇒ **設計軸は「新 C 側 code」に傾く**が **disposition は Rs**。

## 3. 2 件を貫く設計軸原則（Rs が同クラスと見るための注記）

G-4（canonicalization 方式の適合性）と G-6（error code の意味）は**同クラス** = **identity/name が契約要素なのに fungible 扱いされている**。G-4: sort_keys と UTF-16 を「3 実装」と対等視したが凍結 `:168` は 1 適合方式を確定。G-6: 凍結 code 名を別 trigger で再利用したが code は defined trigger を持つ。両件とも pQ が自己 flag 済（v2.4:118 / :75 open-15）。⇒ **「同名/同定数 ≠ 同じ measurement surface / 同じ trigger」**（本 arc 反復の型）。

## 4. 境界・私の残

- 本回答 = 照会 2 問の設計軸 read のみ。⛔**design v2.4 の設計軸 verdict でない**（v2.4 = cycle-3 FAIL 収束方向・doc 側 G-3〜G-13 fold 中・両件は Rs へ routing 済 = verdict §4 (a)-(d)）。
- ⛔**私は key を開かない・部分版 freeze の可否（Rs 判断 (c)）を先取りしない**（NHA/verdict §4 が「承認済境界 5 項なのに 2 項を批准させるのは順序が逆」と明記・私も同意 = 順序を逆にしない）。
- ⛔凍結（D1.1-B fixture・v13）を編集しない。**disposition = Rs**: G-4 = D1.1-B fixture 方式訂正（低緊急・値正）+ identity.py impl（CLOSED）/ G-6 = code identity（新 code 傾く・Rs 決）。
- 私の次レグ = Rs 裁定後の **design 全 fold 版の設計軸 verify**（前提修正・境界・両凍結触りの反映を確認）。**私 = reactive standby**。
