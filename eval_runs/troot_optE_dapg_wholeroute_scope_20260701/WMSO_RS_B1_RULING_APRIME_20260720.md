# ⛔VOID — Rs 裁定 — WMSO D1.1-B / B1 hash 供給 locator = ~~**A′**~~ — custody record

> ## ⛔ 本裁定は **Rs により破棄された**（2026-07-20 15:5x JST）
>
> **Rs 逐語: 「誤りが前提であるならそれは当然破棄にしろ」**
>
> **破棄理由** = 本裁定は、**CC（pQ）が提示した問いに不正確な前置きが含まれた状態**で下された（§2 参照: 「tensor_binding と normalization の両 slot に**同型で効きます**」— 実際は profile 適用が非対称）。
>
> **⚠ CC の誤った対応（記録）**: 私（pQ）と pS は、事後に「不正確部分は A/A′/B の選択に **orthogonal** ゆえ裁定は STANDS」と判定し、Rs には「軽い確認」を求めるにとどめた。**この判定自体が不当だった** — **誤った前提を提示した側が、その誤りが相手の判断に効かなかったと決めることはできない**。判断の権威は Rs にあり、前提が汚染されていた時点で裁定は無効である。orthogonality の分析（§本文および pS §21/§22）が技術的に妥当かどうかは、この結論を変えない。
>
> **本 file の位置づけ**: 破棄された裁定の**歴史記録**として保持する（削除しない）。⛔**本 file を A′ 採択の根拠として引用してはならない。**
>
> **現在の B1 状態 = ⛔OPEN**（Rs 再裁定待ち）。再上程は**訂正済みの前提**で行う（profile 非対称を含む）。
>
> **波及処置**: DESIGN v7/v7.1 の A′ fold = 無効（v8 で B1 を OPEN へ復帰）／pS の v7・v7.1 設計軸 PASS = 無効化／pN exact-pin（v7.1）= 中止依頼（15:55）／LEDGER DDR #27 = p6 へ差し戻し依頼（15:59、commit `470ef27c5e` が STOP 前に着地していた）。

- node: `T-WMSO` D1.1-B; 記録者 = `w2:pQ` RS-TECH-LEAD2（**裁定者は Rs**。本 file は CC による custody 記録であり、裁定内容の権威は Rs にある）
- **裁定受領 = 2026-07-20 14:39 JST**（pQ session 内）／**本 file 作成 = 2026-07-20 15:08 JST**（shell 実測）
- 作成理由 = pS 条件 **C-1**（`WMSO_D11B_DESIGN_VERIFY_WMSODESIGN_20260720.md` §19、sha `a4620ac0449c…` @ `23fac01ec9`）: 「Rs の A′ 裁定の standalone verbatim が未 bank。pN PASS-CLOSE transcript は bank 済（`ccff616b89`）なのと対照。**freeze は A′ を Rs 権威で確定するゆえ freeze 前に bank 推奨**」

---

## 1. 裁定の形式（⚠ honest scope — 逐語 prose は存在しない）

本裁定は **構造化選択（single-select question）** として提示され、Rs が選択肢を 1 つ選ぶ形で下された。**Rs による自由記述の発言は無い。** したがって本 file が保持できる「逐語」は **提示した問い + 選択肢文言 + Rs が選んだ選択肢** であり、prose の引用ではない。この区別を潰して「Rs が『…』と述べた」と書くことはしない。

- 追加の注記（`annotations`）= **無し**（Rs は選択のみ）。

## 2. 提示した問い（逐語）

> D1.1-B の freeze を止めている唯一の gate = hash 供給 locator (B1) の裁定をお願いします。凍結済み ArtifactSlot = {state, artifact_hash} に ref が無く、実測では locator は rank 3 にしか存在しません (最初の slice が動く SHADOW rank 2 には無い)。tensor_binding と normalization の両 slot に同型で効きます。

⚠**本問いの末尾「両 slot に同型で効きます」は、後の実測で不正確と判明した**（OFFLINE_REPLAY は TENSOR_BINDING を免除するが NORMALIZATION は required — §4 表 / pS §19 が独立追認）。**locator gap の構造は同型だが profile 適用は非対称**。裁定内容（A′ 採択・両 slot 対象）はこの訂正によって変わらないが、**Rs は不正確な前置きを含む問いに対して裁定した**ため、ここに loud に記録する。

## 3. Rs が選択した選択肢（逐語）

> **A′ — 凍結済み source_ref を束縛 (推奨)**
>
> frozen EvidenceRecord.source_ref を locator として束縛する。凍結スキーマに手を入れず、全 grade に存在するため SHADOW rank 2 でも成立。3案中で最小変更・最も早く freeze に到達。

（`(推奨)` は **CC が付した推奨マーク**であり Rs の語ではない。Rs は推奨付きの選択肢を選択した。）

**提示した他の 2 択**（不採択・比較のため保持）:
- **A — hash 由来の canonical ref**: artifact_hash から canonical ref を導出。content-addressed store (CAS) が前提になり、`E_BINDING_HASH_MISMATCH` は store 整合性検査に縮退する。
- **B — frozen schema に delta を入れる**: ArtifactSlot に ref を追加。supersession + Rs review が必要で、D1.1-A の凍結パッケージを開けることになる。

## 4. 裁定の適用範囲（本 file が主張すること / しないこと）

**主張する**:
- B1（hash 供給 locator）の解として **A′ を採択**。対象 = **`tensor_binding` + `normalization` 両 slot**。
- 実装形・根拠・profile 別適用・error code の整理 = **`WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md` §4**（v7.1 以降）が正。

**主張しない（境界）**:
- ⛔本裁定は **implementation / training / closed-loop authority を解錠しない**。
- ⛔本裁定は **freeze そのものではない**。freeze には **pN exact-pin（v7 系）PASS-CLOSE** + C-2 の records 反映が別途要る。
- ⛔本裁定は D1.1-C / slice の着手承認を含まない。
- 本裁定は §4 の設計内容を Rs が逐条検証したことを意味しない（Rs は 3 択から locator 方式を選択した）。

## 5. 関連 pin

| 対象 | sha256 / commit |
|---|---|
| DESIGN v7（A′ fold 初版） | `6bbf64b3575f2d0c31422d2163655b56dbadea7c1e3cd35fbde374dabf28626d` @ `a8b9d4004a` |
| pS 設計軸 PASS-WITH-CONDITIONS（§19/§20） | `a4620ac0449c006c02ac6d22890001a0d3710ccf1c6b28b93e9796d257b32a96` @ `23fac01ec9` |
| pN exact-pin PASS-CLOSE（v6.1・A′ 以前） | `a31498dd0582ae612f22d4f04b8f4fce5ca989e9932b44e91a54c15d975aa473` @ `ccff616b89` |
| frozen D1.1-A（不変） | DESIGN `00192d20ca00b654…` / EP md `c474acea7c58…` / EP JSON `e63176af9bc3…` |
