# WMSO D1.1-C — Rs routing（判断依頼 4 件）

- 起草 = `w2:pQ` RS-TECH-LEAD2（node `T-WMSO`）／**2026-07-21 17:4x JST**（shell 実測）
- 契機 = debate **cycle-3 = FAIL**（`d23e5faaa8d61273…` @ `acce4d5c79`）§4。NHA の最小十分案 =「**two-key を開かず、Rs へ 1 通で routing し、新規 design text を足さない**」
- 対象 design = **v2.2 + v2.3 追補**（`eb956c55aaa61802…` @ `1c817ce1df`）／fixtures = builder `1c4eebff59c520c8…` @ `55705bfa56` + golden 4 本 @ `e1ed170014`
- ⛔**本 doc は判断しない**。判断は Rs。私は事実と選択肢のみを置く。

---

## (a) 凍結 D1.1-B v13 `:256` / `:471` の併記訂正 — ✅**裁定済（Rs = 「B」= 別 artifact で訂正・凍結物は編集しない）**

⇒ 履行 = `WMSO_D11B_COCITATION_CORRECTION_NOTE_20260721.md`。⛔**凍結物の sha は不変**（`5a1874d3be8b98b8…`）。⛔**(b) は本裁定で動かない**。

**事実**（pQ 実測・pS 設計軸 read・pY custody 再測の 3 者が一致）:
- v13 `:256` 逐語「`proof_policy._domain` = 「exact required ProofKind set」＋ `E_PROOF_KIND_FOREIGN`」。同行に「**D-3 に合流**」も在る。
- 凍結 EP md `:114` は `E_PROOF_KIND_FOREIGN` を「**component に意味を持たない kind の混入**」＝ **component 意味論**と定義。`:129(iii)` の例示も同様。
- `TRAIN_RUN_MANIFEST` は EXACT **13/13** cell で required ⇒ どの component にも意味を持つ ⇒ 非 foreign。
- 凍結 4 file に **set-equality / 超過拒否の規則は無い**（proof 系 error 語彙 7 種を閉じた列挙・`superset`/`excess`/`extraneous` = 4 file とも 0 hit）。

⇒ **`:256`/`:471` の `E_PROOF_KIND_FOREIGN` 併記は、凍結 EP の定義と整合しない。**
**判断事項** = 凍結 file の訂正可否と方法（**凍結編集は Rs 専権**。pQ・pS・pY のいずれも編集していない）。

## (b) 採択 D-1 への影響

**事実**:
- foreclose された案は「**rank 2 に proof kind を追加要求**（= required set の拡張）」で、`:256` は「**D-3 に合流**」＝ **frozen schema delta を要する**ことを決定脚に挙げている。
- 採択 D-1 の積極根拠 `:252` = 「frozen delta 不要／1 hop／B 側宣言 1 個／contracts_v2 `:396` の provenance 意味論適合」— **proof kind 集合への言及なし**。
- D-1 自身の反証条件 `:258-262` = `source_ref` 意味論／registry 衝突／resolver 到達性／1 hop — **proof kind 集合への言及なし**。
- 当該 arc に **Rs ratify 2026-07-20 21:44** が乗っている。

⇒ ⛔**pQ・pS・pY のいずれも「D-1 が覆る」とも「不変」とも宣言していない**（誤前提を出した側に immaterial を決める standing が無いため）。
**判断事項** = D-1 の帰趨の正式判断。

## (c) 部分版の扱い（⭐問いを立て直したもの）

**⚠ 以前の問い方は誤りだった**（cycle-3 G-10）: 私は「**承認済 scope（IN 5 項）を 2 項へ縮小してよいか**」と上程したが、design §8 open-1 は「**後続版で設計する**」＝ chunk 内の先送りであり、**縮小ではない**。**多版 authoring は D1.1-B v1..v13 が同一 prereg の下で行った先例**がある。

**正しい問い（2 つ）**:
1. **部分版（prereg IN 5 項のうち 2 項＋部分 1 項）で two-key を開いてよいか。**
   - ⚠ pS の設計軸は prereg §5-1 で「**IN-OUT 境界が機構-policy 線で正しく切れているか**」と定義されている。承認済境界は 5 項。**2 項の境界を批准させるのは順序が逆**（NHA 指摘）。
2. **IN-1 / IN-3 / IN-4 / U-2 / U-6 を open に残したまま freeze してよいか。**
   - 先例 = D1.1-A も D1.1-B も **declared open を残して freeze**している（v13 `:493`）。

⚠**付随事実（cycle-3 G-5）**: prereg **IN-2 も部分履行**である。IN-2 逐語は「silent pooling を**禁止**する（検出・拒否の code を含む）」だが、設計は「列挙の網羅性は記録単体から判定不能」として**保証を撤回**した（open-9）。⇒ 「2 項設計済」も正確には **1 項 + 部分 1 項**。

## (d) open-5 の owner 指名 — ⛔⛔**下記の前提 1 件を撤回**（2026-07-21 18:4x）

⭐**撤回**: 「**D1.1-B fixture も非適合＝第 2 の凍結波及**」は**誤り**でした（pY が実測で反証・custody `641229b6d6f18b3f…` @ `bb7fd7cc19`）。同 fixture は `:198` で **ASCII-key assert** を持ち乖離は到達不能、かつ**凍結 `:171` 自身が (b) typed 入口＝ASCII-key assert の層を定義**しており、fixture は**その層の実装**です。⇒ ⭐**凍結 chunk 内に確認された非適合は無く、(d) は凍結波及ではありません**。⚠ 機序 = 私が `:208` の 1 行だけを読み、囲む関数と凍結 `:171` を読まずに一般化した（§1 の誤りと同型）。

⇒ **残る論点は `identity.py:80-82` のみ**で、これは別用途の canonicalizer（`finetune_cfg_hash` / handoff payload hash・§168 を参照しない）ゆえ「**§168 に一致すべきかの設計問題**」（pS + pQ・latent）。**Rs 判断としては (d) を取り下げ可**。

**事実**（cycle-3 G-4 で読みが変わった）:
- 凍結 contracts_v2 `:168` が **key 順を逐語で決めている**（「object key sort = UTF-16 code unit 順（`k.encode("utf-16-be")` bytes 昇順）」）。
- `thread_isaac_lab/wmso/d1/identity.py:80-82` の `canonical_json()` = `json.dumps(sort_keys=True, …)` = **codepoint 順** ⇒ **凍結規則に非適合**。
- **D1.1-B fixture の `wcj_bytes` も同じ挙動**（`sort_keys=True`）⇒ **凍結 / CUSTODY-CLOSED chunk 内の非適合**。
- ⇒ 「**3 実装が併存**」ではなく「**2 挙動 / 3 site で、凍結規則に適合しているのは D1.1-C の 1 つだけ**」。実測: 同一入力に対し WCJ = `{"😀":2,"！":1}` ／ 他 2 site = `{"！":1,"😀":2}`。
- ⚠ 現行 corpus は全 ASCII のため**差は顕在化していない**（latent）。

⇒ **これは「どちらが正か未決」ではなく「非適合の是正」の問題**である可能性が高い。
**判断事項** = 是正の owner 指名と、**D1.1-B（凍結）側の扱い**（(a) と同型の凍結波及）。

---

## 参考: 本 routing が変えないもの

- ⛔**impl / training / closed-loop authority / push / freeze / slice = CLOSED 継続**。
- ⛔**凍結 4 file は未編集**（sha 4/4 不変を実測）。
- **two-key は開いていない**（pS / pY へ key 依頼を出していない）。
- 本 routing は **design text を 1 行も足していない** — (a)(b) は design §1.1、(c) は §0/§8 open-11、(d) は §6/open-5 に既記載のものを 1 通にまとめただけ。
