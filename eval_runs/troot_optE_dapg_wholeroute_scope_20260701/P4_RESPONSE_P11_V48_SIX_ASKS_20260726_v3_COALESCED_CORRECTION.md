# p11 v4.8 六件回答 — p4 **v3（coalesced correction chain）**

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 17:41:38 JST（date-THEN-write）。
**応答先:** pN RETURN `…-20260726-001`（B1-B4 = v2 で対応）＋ **ADDENDUM `…20260726T1739JST-002`（B5 / B6）**。本書は **①と③を現行版へ置換**する（②④⑤⑥ は PASS 済で不変）。
**⛔ 履歴 rewrite なし** — v1 `c69a3015a0`（sha256 `f4acf0e72c507749…`）／v2 `1d11e86a6a`（sha256 `a5043daf68140b28…`）は削除も改変もしない。

## 0. correction chain

| 旧（保全） | 該当箇所 | 訂正版 |
|---|---|---|
| v1 `c69a3015a0` | §① 「唯一の live surface = report `:7522` の key」／接地「banked HEAD」 | **§B1** |
| v2 `1d11e86a6a` | §① 「1 file・1 schema surface・2 instances」（**まだ狭い**） | **§B1** |
| v1 `c69a3015a0` | §③ 「**Rs 承認は不要**（制御則を変えない限り）」 | **§B2** |

**影響先:** pN（提出）／Rs（私の 17:33・17:39 報告）。⇒ Rs へは直接訂正する。

## A. 維持（変更しない）

②④⑤⑥（PASS 済）／**class B = HOLD**／source・実装・RUN・verify・status **未解錠**。
① のうち維持: 文書側 hit は**撤回文脈**／`8.838` の `forkb_e0v2_*` は **false positive**（`window_steps_per_s`）／`ζ 2.857` は **provisional 明記**／`27.22` の current 根拠は **`:232`/`:234`**（`shoulder_lift` に載る・Jacobian 非経由ゆえ非撤回）。

## B1. §① の scope を完成 — **2 paths / multiple instances**

**接地（moving ref を廃止）:** scanned commit = **`c69a3015a0e17ab3819bab59afed4e390af8d8a6`**／command = `git show <commit>:<path>` による直読／report blob = **`8b9ccfbe73965b415d26de4f1db77e4f6c181e40`** / sha256 = **`4cb02e3b798e9a1e354f9646597593ce86053705251755581933deec401a2a9d`**。

⛔ **撤回:** v1「**唯一の** live surface = report `:7522` の key」／v2「**1 file・1 schema surface・2 instances**」— **いずれも狭すぎた**。

⭐ **訂正 = 2 paths（私の実測）:**

| path | 実測した instance |
|---|---|
| `arm_control_measurement_h2_report.json` | `:6406` **note**（"Multiply Dq … to get tip droop in mm"）／`:7504` **object** `static_tip_droop_H3_1_x_H4`／`:7509` **formula** `droop_mm = sum_i |J_a_trans_i [mm/rad]| * |Dq_i [rad]|`／`:7516`・`:7522` `droop_mm_sum_of_abs`／`:7517`・`:7523` `droop_mm_worst_single_joint` |
| `arm_control_measurement_harness.py`（⭐**生成器**） | `:842` prose コメント／`:871` note 文字列／`:1561-1562` key 代入と `static_tip_droop(...)` 呼び出し。**同 file の `droop` token = 9 件**（私の実測） |

⭐ **生成器を含めるべき実質的理由:** **report だけ直しても再生成で元に戻る。** ⇒ **p0 の cause-side 訂正 scope は report ＋ harness の両方**。
⛔ ただし **[CHANGE] は HOLD**（source CLOSED）。⛔ 私は**代理編集も実装 authorization もしない**。

## B2. §③ の authority overclaim を撤回

⛔ **撤回:** 「**Rs 承認は不要**（制御則を変えない限り）」。

**なぜ誤りか — 私自身が書いた brief と矛盾する:**
`ARM_CONTROL_DESIGN_ROLE_BRIEF_p11_20260721.md`
- `:58` 「07-Design / 04-Specs は read-only（**正式採用＝Rs**）。あなたは **提案として bank** し、**canonical 採用は p4 経由で Rs へ上げる**。」
- `:67-68` 「1. …**提案として bank**・p4 経由で Rs へ ／ 2. **L3 ＋ 設計ゲート ＋ `/pre-check`** を通す ／ 3. **Rs 承認後、p4 が p0 へ実装を渡す**。」

⇒ 私は **(i) 分類**（gain は制御則でなくパラメータか）と **(ii) 採用権限**（canonical 採用・実装 authorization は誰か）を**混同**した。

⭐ **訂正 = 正しい分割:**

| 段 | 誰 / 何 |
|---|---|
| gain の **選定・提案** | **p11**（設計 court） |
| 必須 gate | **`/force-design`** ＋ **L3**（`task_config.py` に触れるため）＋ 該当する **`/pre-check`** |
| **canonical 採用 / 実装 authorization** | **記録上の Rs leg を保持**（brief `:58` / `:67-68`）⇒ **p11 提案 → p4 → Rs 承認 → p4 が p0 へ渡す** |

⚠ **(i) の分類自体は維持**（`ke` のみ／`ke`＋`kd` 同時 の別は court を変えない・`CLAUDE.md` DiffIK 節）。**ただし分類は採用権限を変えない。**
⛔ 私は **superseding authority pin を提示できない**ため、**Rs leg を落とさない**。

## C. 非主張（不変）

- ⛔ 本書は H-3.1 GO / H-4 全体 / source / 実装 / RUN / verify / status を解錠しない。class B は別 leg で HOLD。
- ⛔ 他 pane の record を代理編集しない（① の 2 path はいずれも **p0 の court**）。
- ⛔ 物理妥当性は判定しない（Rs 動画が最終基準）。

---
**p4 v3 coalesced correction = 2026-07-26 17:41:38 JST / RS-TECH-LEAD (`w2:p4`)**
