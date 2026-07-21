# WMSO D1.1-B（凍結）`:256` / `:471` の併記に対する訂正 note

- 起草 = `w2:pQ` RS-TECH-LEAD2（node `T-WMSO`）／**2026-07-21 18:3x JST**（shell 実測）
- **authority = Rs 裁定 (a) = 「B」**（逐語・本 pane で直接受領・relay 0 hop）= 「**凍結物を編集せず、別 artifact で訂正を述べる**」。選択肢は A 編集しない／B 別 artifact／C 直接編集の 3 択で提示し、**Rs が B を選択**した。
- ⛔⛔**本 note は凍結物を編集しない**。対象 file の sha256 は `5a1874d3be8b98b8…` のまま**不変**（起草時点で実測・working tree clean）。**この sha を pin する repo 内 11 面はいずれも動かない**。

## 1. 対象（凍結 / CUSTODY-CLOSED）

`WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md`（DESIGN v13・`5a1874d3be8b98b8…` @ `07250f4a02`）の 2 行。

**`:256`（一次 locus・D-1..D-4 選定表の落選行）逐語**:
> `| rank 2 への proof kind 追加 | ⛔**FORECLOSED** | `proof_policy._domain` = 「exact required ProofKind set」＋ `E_PROOF_KIND_FOREIGN`（`B1D-A`）。B 側 spec では不可・D-3 に合流 |`

**`:471`（縮約再掲）逐語**:
> `…／rank 2 への proof 追加 = **FORECLOSED**（`_domain` = exact set + `E_PROOF_KIND_FOREIGN`）。`

## 2. 訂正の内容 — **併記された `E_PROOF_KIND_FOREIGN` は根拠にならない**

凍結 EP markdown（`c474acea7c58acc2…`）が同 code を **component 意味論**として定義している:
- `:114` 逐語「…**component に意味を持たない kind の混入** = `E_PROOF_KIND_FOREIGN`」
- `:129(iii)` 逐語「**他 component 向け kind の混入（例: POLICY_ARTIFACT claim に INPUT_SCHEMA_HASH）→ E_PROOF_KIND_FOREIGN**」

`TRAIN_RUN_MANIFEST` は EXACT の **13/13 cell で required**（pQ 実測）＝ **どの component にとっても意味を持つ** ⇒ 非 foreign。
加えて **凍結 4 file に set-equality / 超過拒否の規則は無い**（proof 系 error 語彙 = `ARTIFACT_UNRESOLVED` / `CONFLICT` / `INSUFFICIENT` / `KIND_FOREIGN` / `MISBOUND` / `PAYLOAD_MISSING` / `REF_MALFORMED` の 7 種で閉じた列挙。`superset` / `excess` / `extraneous` = **4 file とも 0 hit**）。⚠**誠実な範囲 = error code 語彙上の不在**であり、散文規則の不在までは主張しない。

⇒ **`E_PROOF_KIND_FOREIGN` は「required set を超えて proof を携行できない」ことの根拠にならない。**

## 3. ⭐ 決定脚は健在 — foreclose の結論は本 note では動かない

`:256` の option 名は逐語で「rank 2 への proof **kind** 追加」＝ **required set の拡張**である。同セルは「**D-3 に合流**」＝ **frozen schema delta を要する**と述べており、**これが決定脚**。delta 要求は本 note の訂正と独立に成立する。

⚠ `:471` は縮約再掲で、option 名から「kind」が、集合の呼び方から「required ProofKind」が落ちている（「proof 追加」「exact set」）。⇒ **`:256` より広く読める**ため、引用は `:256` を一次とすること。

## 4. ⛔ 本 note が述べないこと

- ⛔**採択 D-1 の帰趨を判定しない**（= Rs 判断 **(b)**・未裁定）。pQ・pS・pY のいずれも「覆る」とも「不変」とも宣言していない。誤前提を出した側にその誤りが immaterial だと決める standing は無いため。
- ⛔**凍結物の status を変えない**。D1.1-B は **FROZEN / CUSTODY-CLOSED のまま**。
- ⛔**freeze record を編集しない**（同 record 逐語「**DESIGN v13 / builder / fixture は status 更新のためにも再編集しない**」）。**freeze record = 時点 snapshot / 現況 = LEDGER** という既存 convention に従う。

## 5. 検証の所在（本 note 自身は未検証）

- **誤りの発見** = D1.1-C design v1 の中心前提が FALSE と判明した過程（cycle-1 判定 `9851f165a5fc45eb…` @ `7f6d038a30`）。
- **設計軸** = pS consult `b4ec93173db6c24c…` @ `a31adca295`（「反証は正しい・前提 FALSE」／併記は「不正確だが冗長な二次引用」と設計軸 read）。
- **evidence 軸** = pY custody `b602a8c8030d47a7…` @ `337d08d787`（逐語 3 本を独立再測・faithful／一次 locus は `:256` と指摘）。
- **pQ 実測** = 上記 §2 の列挙・EXACT 13/13・`:256`/`:471` の逐語。
- ⚠**本 note 自体は two-key を経ていない**。設計軸 / evidence 軸の批准は pS / pY へ回す。

## 6. 参照させる面

- `00-DESIGN-STATUS-LEDGER.md`（D1.1-B 行 + §DDR）から本 note を指す — **反映は p6 court**。
- D1.1-C design v2.4 §1.1 は本 note を一次参照とする。
- routing `WMSO_D11C_RS_ROUTING_20260721.md` の **(a) = 裁定済（B）**。
