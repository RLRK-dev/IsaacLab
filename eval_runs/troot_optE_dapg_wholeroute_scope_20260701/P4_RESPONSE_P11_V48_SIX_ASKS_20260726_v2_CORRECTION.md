# p11 v4.8 六件回答 — p4 **v2 correction chain**

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 17:37:30 JST（date-THEN-write）。
**応答先:** pN RETURN `MSG-PN-P4-P11V48-RESPONSE-RETURN-20260726-001`（records/authority 4 件）。
**⛔ 履歴 rewrite なし** — v1 は削除も改変もしない。本書が該当箇所を RETRACT / 精密化する。

## 0. correction chain

| 旧（維持・改変しない） | 該当箇所 | 影響先 | 訂正版 |
|---|---|---|---|
| `P4_RESPONSE_P11_V48_SIX_ASKS_20260726.md` @ `c69a3015a0`（sha256 `f4acf0e72c50774998e51c1e611a58e4239ce39380c5f17193a829501ada9fe4`） | §① の接地「**banked HEAD**」 | pN（提出）／Rs（私の 17:33 報告） | **§B1** |
| 同上 | §① の「**1 件**」 | 同上 | **§B2** |
| 同上 | §① の `27.22` 根拠 = design **`:208`** cite | 同上 | **§B3** |
| 同上 | §④ の owner 候補（p17 欠落） | 同上 | **§B4** |

## A. 維持（変更しない）

§① の**結論**（live surface は **h2 report の 1 面のみ**・文書側は撤回文脈・`8.838` の `forkb_e0v2_*` は false positive・`ζ 2.857` は provisional 明記）／**②③⑤⑥ の裁定**／**class B = HOLD**／source・実装・RUN・verify・status **未解錠**。

## B1. 接地を moving ref から producing commit へ

⛔ **撤回:** 「**banked HEAD** で `git grep`」= **moving reference**（HEAD は動くため後日再現しない）。
⭐ **訂正 = producing commit に接地**（私が独立に再計算し一致）:

| 項目 | 値 |
|---|---|
| 実査を接地する commit | **`c69a3015a0e17ab3819bab59afed4e390af8d8a6`** |
| `arm_control_measurement_h2_report.json` の blob | **`8b9ccfbe73965b415d26de4f1db77e4f6c181e40`** |
| 同 sha256 | **`4cb02e3b798e9a1e354f9646597593ce86053705251755581933deec401a2a9d`** |

## B2. 「1 件」→ **1 file / 1 schema surface・2 instances** に精密化

⭐ **実測（上記 blob 上）:** `droop_mm_sum_of_abs` は **2 occurrence**。

| 行 | 値 |
|---|---|
| `:7516` | `14.593809385312591` |
| `:7522` | `4.074094093154737` |

⇒ 正確形 = **live surface は 1 file（1 schema）だが instance は 2 つ**。**p0 の訂正対象は両方**（片方のみ直すと同一 schema 内に不整合が残る）。⛔ 私は代理編集せず、実装 authorization も出さない（source CLOSED）。

## B3. `27.22` の根拠 cite を差し替え（stale を current として引いた）

⛔ **撤回:** design `:208`「**どの関節が 27.22 を負うかは未測**ゆえ両方を出す」を **current** として引用したこと。
**理由:** 同 design `:234` が「旧記載『①どの関節が 27.22 を負うか未測（H-3.1 待ち）』は **stale かつ自己矛盾**だった」と**明示的に撤回**している（`0f373bedbd` 以降・pN の C3 受理）。⇒ 私は**撤回済みの記述を現行根拠として引いた**。

⭐ **訂正 = current は `:232` / `:234`:** 「✅ **撤回しないもの**（**Jacobian を経由しない量**）= `τ_bias` の最大 **27.22 N·m が `shoulder_lift`（`ke = 2000`）に載る**こと、および **`Δq = 13.61 mrad`**」。
⇒ **結論は不変**（`27.22` は「確定値の誤用」に当たらない）が、**理由が変わる**:
- ⛔ 旧理由「**未測ゆえ限定つき**」= 誤り。
- ⭐ 正しい理由 = **負担関節は確定済（`shoulder_lift`）であり、撤回されたのは Jacobian を経由する mm 換算のみ**。⇒ `27.22` と `Δq = 13.61 mrad` は**保持されている量**として引用してよい。

## B4. `W-b` owner 候補に **p17** を追加・p16 を精密化

⭐ **訂正:** 候補集合に **`p17`（SKILL-DESIGN）を追加**する。user directive により **SKILL の分解・粒度・unit/composition は p17 の scope key** であり、W-b の waypoint 集合はその境界に触れ得るため。**`p16`（MWSO-DESIGN）は contract/schema delta 時のみ**に精密化。
⇒ **境界照会の候補 = `p5` / `p11` / **`p17`** / `Rs`**（`p16` は contract/schema delta 時のみ）。
⛔ **owner は UNCONFIRMED のまま**（cause-side 指令: 未確定なら帰属を捏造しない）。私は割り当てない。⚠ **非 blocking** も不変（p11 自身が (1)(2) は waypoint 確定前でも進むと明記）。

## C. 非主張（不変）

- ⛔ 本書は H-3.1 GO / H-4 全体 / source / 実装 / RUN / verify / status を解錠しない。class B は別 leg で HOLD。
- ⛔ 他 pane の record を代理編集しない（① の h2 report は **p0 の court**）。
- ⛔ 物理妥当性は判定しない（Rs 動画が最終基準）。

---
**p4 v2 correction = 2026-07-26 17:37:30 JST / RS-TECH-LEAD (`w2:p4`)**
