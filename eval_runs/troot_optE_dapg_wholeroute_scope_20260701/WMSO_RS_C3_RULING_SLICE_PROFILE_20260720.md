# Rs 裁定 — WMSO D1.1 slice / C3 EP evidence profile = **SHADOW（rank 2・非 authority）** — custody record

- node: `T-WMSO`; 記録者 = `w2:pQ` RS-TECH-LEAD2（**裁定者は Rs**。本 file は CC による custody 記録であり、裁定内容の権威は Rs にある）
- **裁定受領 = 2026-07-20 18:5x JST**（2 回目・有効）／**本 file 作成 = 2026-07-20 18:57 JST**（shell 実測）
- **対象**: boundary-only vertical slice が目標とする **EP evidence profile**。⚠**execution profile（boundary-only / real-time）とは別軸**（`WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md:13` は前者を述べる）。

---

## 1. 裁定の形式（honest scope）

**構造化選択（single-select）**。**Rs の自由記述 prose は存在しない**。本 file が保持する「逐語」は **提示した問い + 選択肢文言 + Rs が選んだ選択肢**であり、prose 引用を捏造しない。追加注記（annotations）= 無し。

## 2. ⛔ 1 回目の裁定（17:57）は破棄 — 結論が一致しても無効

| | 1 回目（⛔VOID） | 2 回目（✅有効） |
|---|---|---|
| 時刻 | 2026-07-20 17:57 | 2026-07-20 18:5x |
| 選択 | SHADOW | SHADOW（**同一**） |
| SHADOW の characterization | ⛔「**実機に出さず policy を並走させる形**」= **CC の未検証の言い換え**（凍結側に該当記述なし） | ✅「**非 authority**」= 凍結逐語（EP md `:136` 表見出し「SHADOW（非 authority）」／`:155`「SHADOW は定義上 非 authority」） |
| 帰趨 | **Rs が破棄**（逐語「**前提が違ったので選び直す**」） | 有効 |

⭐**記録すべき規律**: **結論が一致しても、誤った前提の上の裁定は無効**。1 回目を「結果的に同じだから有効」と扱わない。これは 2026-07-20 の A′ 裁定破棄（Rs 逐語「誤りが前提であるならそれは当然破棄にしろ」）で確立した規律の 2 例目であり、**「不正確部分が選択に orthogonal でも救済されない」**という含意もそのまま適用される。

⚠**1 回目の経緯（CC 側の自己記録）**: 誤りは **CC が preview に書いた運用的言い換え**であり、pS/pN の指摘ではなく **CC が裁定受領後・伝播前に自ら検出**した。前回（A′）は指摘を受けてなお「orthogonal ゆえ有効」と誤判定したが、今回は **自判定せず Rs に上げた**。ただし**そもそも未検証の言い換えを判断材料に混ぜたこと自体が defect** である。**pS / pN / p6 への伝播は 0 件**（破棄時点で未 dispatch）。

## 3. 提示した問い（2 回目・逐語）

> （再提示）boundary-only vertical slice の目標 **EP evidence profile** をご指定ください。今回の各選択肢の記述は **凍結パッケージの逐語または two-key 検証済の実測のみ**で、私の言い換えを含めていません。前提：profile は「required set + min_grade」の宣言であり、usage matrix = ceiling（天井）です。

## 4. Rs が選択した選択肢（逐語）

> **SHADOW（rank 2・非 authority）**
>
> 凍結逐語「SHADOW は定義上 非 authority」。両 slot required だが rank 2 に target-byte locator が無いため B1 を正面から解く必要がある。

**不採択（比較のため保持）**: **CLOSED_LOOP（rank 3）** — 凍結逐語「acceptance test 後に可」row・rank 3 に locator あり ／ **OFFLINE_REPLAY（rank 2）** — 凍結逐語「replay does not re-execute binding」により TENSOR_BINDING 免除。

## 5. 裁定の前提（**two-key 検証済**）

**premise claim-set v6** = `40e5ca3bb09de3e1c632809e785bd6ed94a9941c3b31ba32067ba10eeac4483a` @ `99a1fc5c6a`
- **pS 設計軸検証** = `9937f2d01fccc8863b53bcc228002793061c0f639d24dac7caf6364f210c20b0` @ `16ef235c20`
- **pN exact-pin EVIDENCE PASS-CLOSE** = 2026-07-20 17:53:58（C1/C2/C3/C4a/C4b 全 TRUE・選択肢 0/推奨 0 を確認）

| claim | 内容 |
|---|---|
| C1 | frozen `ArtifactSlot = {state, artifact_hash}` に locator field 無し |
| C2 | **軸 B（target-byte locator）= rank 3 のみ** ／ 軸 A（hash association）= rank 3 + rank 4 |
| C3 | slice の EP evidence profile は統治文書に**規定 0 件**（＝本裁定が埋める空白） |
| C4a | **schema 層**（`ArtifactSlot` / `claim_targets`）では両 slot 同型 |
| C4b | **end-to-end では非同型**（NORM は rank 4 に locator あり・TB 無し／OFFLINE_REPLAY は TB のみ免除） |

**profile の凍結定義**（EP md §4「Usage profiles（required set + min_grade）」・`:154`-`:156` 逐語要旨）: profile 充足 ⇔ 免除されない全 required component の達成 grade ≥ min_grade ／ **usage matrix = ceiling** ／ **closed-loop authority は O0/S0/V0 two-key + 独立安全 gate を必ず conjoin** ／ profile 単調 = CLOSED_LOOP ⊇ SHADOW ⊇ OFFLINE_REPLAY（免除前）。

## 6. 本裁定の帰結（事実）

- slice の目標 profile = **SHADOW（min_grade_rank 2）**。**TENSOR_BINDING・NORMALIZATION とも required**。
- ⇒ **B1（hash 供給 locator）は回避されず、rank 2 で解く必要がある**。**rank 2 には frozen の target-byte locator が存在しない**（C2）ため、**B1 は本 slice の必須解決事項**。
- ⇒ **OFFLINE_REPLAY を選んだ場合に生じたはずの「TB locator 不要」という逃げ道は取らない**という決定でもある。

## 7. 本裁定が主張しないこと（境界）

- ⛔**B1 の解法を選んでいない**。A/A′/B（旧 3 択）は **A′ 裁定破棄に伴い集合ごと未確定**であり、**SHADOW 要件から改めて導出する**。本裁定はその**上流の前提を固定しただけ**。
- ⛔**implementation / training / closed-loop authority を解錠しない**（凍結逐語のとおり closed-loop authority は別 gate の conjunction を要する）。
- ⛔D1.1-C / slice の着手承認を含まない。
- ⛔**execution profile（boundary-only / real-time）を決めていない**（別軸）。
- ⛔slice の run timing（B/C 完了後のどの時点か）を決めていない。

## 8. 関連 pin

| 対象 | sha256 / commit |
|---|---|
| premise claim-set v6 | `40e5ca3bb09de3e1c632809e785bd6ed94a9941c3b31ba32067ba10eeac4483a` @ `99a1fc5c6a` |
| pS 設計軸検証 | `9937f2d01fccc8863b53bcc228002793061c0f639d24dac7caf6364f210c20b0` @ `16ef235c20` |
| DESIGN 現行（B1 = OPEN） | v8 `452f8d2484af174d993cc07e124d1e833060ec5847b65d74f2c5c3858f3382ce` @ `ff2be80ab0` |
| ⛔VOID: A′ 裁定記録（引用不可） | `WMSO_RS_B1_RULING_APRIME_20260720.md` |
| frozen D1.1-A（不変） | DESIGN `00192d20ca00b654…` / EP md `c474acea7c58…` / EP JSON `e63176af9bc3…` |
