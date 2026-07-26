# p11 v4.8 §2 の依頼 6 件 — p4 court の裁定 / readback

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 17:31:17 JST（date-THEN-write）。
**対象（私が独立照合・一致）:** `P11_ROUTING_SUBMISSION_20260726_ARMCONTROLDESIGN.md` @ `e426d97d189ca1f4e7e0ddfe6cf7f10312cf3838` / sha256 `3ebb155f1c1aaa569d5986b236b75b31627551a5732b36e16286bf6b7e13867a`。
**⛔ 本書は H-3.1 GO / H-4 全体 / source / 実装 / RUN / verify / status を解錠しない。** class B は別 leg で `:67`/`:72` reconciliation まで HOLD。

## ① 撤回済・未確定の値を「確定値」として引用している面 — **1 件あり**

**実査（banked HEAD で `git grep`）:**

| 対象 | 結果 |
|---|---|
| 撤回済 mm（`14.594` / `4.074` / `8.838`） | 文書側の hit は**すべて撤回・隔離の文脈**（p11 `:19`/`:114`、p11 design `:230`、私の v1 `:37` は v2 で撤回済）⇒ **確定値として主張している文書は無い** |
| ⚠⚠ **`arm_control_measurement_h2_report.json:7522`** | key 名が **`"droop_mm_sum_of_abs": 4.074094…`** ⇒ **フィールド名自体が「たわみ mm」という R9 で撤回済の解釈を主張**している。**唯一の live surface**。**owner = p0**（artifact 著者）⇒ cause-side で **p0 が訂正**（改名 or 注記）。⛔ 私は代理編集しない・**実装 authorization も出さない**（source CLOSED） |
| `8.838` の `forkb_e0v2_*` 2 件 | **false positive**（`window_steps_per_s` ＝ 別量）⇒ 指摘に含めない |
| `27.22` | p11 design が**限定つき**で提示（`:208`「どの関節が 27.22 を負うかは未測ゆえ両方を出す」／`:232`「撤回しないもの = `τ_bias` 最大 27.22 が `shoulder_lift` に載ること」）⇒ **確定値の誤用に当たらない** |
| `ζ 2.857` | spec が **provisional と明記**（`0025fd32b6` 逐語「Mark the H-2 numbers provisional …」）⇒ 問題なし |

⇒ **回答 = 1 件**（h2 report の key 名）。それ以外は**無し**。

## ② §5.5.D（掃引方法）の p0 回付可否 — **不可（現時点）**

pN operative state で **source / 実装 / RUN / verify が CLOSED**、かつ **H-3.1 = GO 無し**。§5.5.D は掃引＝**実装を伴う**ため、回付は解錠後。⛔ **私からも送らない**（p11 が送っていないのと同様）。
**解錠順序** = pN が解錠 → **私が p0 へ回付** → p0 実装 → pZ 検証。

## ③ ゲイン変更の gate 所在 — **p11 の設計 court**（制御則を変えない限り Rs 承認は不要）

**根拠（`CLAUDE.md` DiffIK 節）:** 「**到達性・収束性の問題は `task_config.py` のパラメータ調整で解決**」＝ gain は**パラメータ**／「**制御方式の変更は rs 承認なしに行わない**」＝ Rs が要るのは **制御則そのもの**を変える時。
⇒ **`ke` のみ / `ke`＋`kd` 同時 の別は court を変えない**（どちらもパラメータ）。
**必須 gate** = **`/force-design`**（力・剛性パラメータ変更の強制ゲート）＋ **`/pre-check`**（GPU 消費前）＋ `task_config.py` に触れれば **L3 自動昇格**。
⚠ **Rs 承認が要るのは制御則の変更**（例: 重力補償の採用 = §0#3。**私が既に上程済**）。

## ④ `W-b` の operative な waypoint 集合と owner — **UNRESOLVED を確認・⛔ owner を捏造しない**

私も banked を検索したが、**waypoint 集合を定める artifact は特定できなかった**（p11 の記述と一致）。
⇒ **境界照会として pN 経由で回す**（fingertip の B/C と同型）。候補 = **p5**（SKILL 詳細設計）／**p11**／**Rs**（W-b の選択自体が Rs 裁定）。⛔ **私は割り当てない**（cause-side 指令: 未確定なら帰属を捏造しない）。
⚠ **非 blocking**: p11 自身が「**(1)(2) は waypoint 確定前でも進む・(3) のみ着手不能**」と明記している。

## ⑤ spec v1.7 の訂正 — **readback PASS**

**私の独立照合:** 同 commit の spec sha256 = **`5d6ba7403a90047d361f39fefbf72dbb97831123fafb68fdbfc93c7a310b3bc8`**（pN pin と一致）。
**内容確認:** `:158` で旧「`body_label` から発見」を**撤回**し、**(i) SSOT 定数から index 解決**（`task_config.py:37` `GRIPPER_PAD_BODY_IDX = [9, 13]`・逐語 "pad-carrying followers"）＋ **(ii) `shape_label` の親 body** の 2 規則へ差替済。`:8` に **⛔「本 spec は実装 gate ではない」**（接地 `:238`）を明記済。
⇒ **私の R8 裁定（`442f58678359bf85`）の RETURN は spec owner 側で履行された。** ⚠ `harness.py:928` の literal `(9,13)` 修正を求めていない点も確認（＝**実装ゆえ未認可のまま・私の court で保留**）。

## ⑥ 正しいたわみ量算出の authorization — **今は出せない**

**理由** = (i) pN operative state で **source / 実装 CLOSED**、(ii) **式・名称・bar の設計裁定が p11 court で未了**。
⇒ **解錠順序** = (i) **p11 が式・名称・bar を裁定** → (ii) **pN が source/実装を解錠** → (iii) **私が p0 へ回付**。
⛔ それまで **p0 は着手しない**（p0 の「authorization 待ち」表明と整合）。

## 非主張

- ⛔ 本書は H-3.1 GO / H-4 全体 / source / 実装 / RUN / verify / status を**解錠しない**。class B は別 leg で HOLD。
- ⛔ 他 pane の record を代理編集しない（① の h2 report は **p0 の court**）。
- ⛔ 物理妥当性は判定しない（Rs 動画が最終基準）。

---
**p4 response = 2026-07-26 17:31:17 JST / RS-TECH-LEAD (`w2:p4`)**
