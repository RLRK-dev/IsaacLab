# D1.1-B freeze — OPS-SUP consultation（pY・Rs 上程用）

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**発行:** 2026-07-21 10:5x JST。
**契機:** Rs「go」（2026-07-21 10:5x）で本 leg 実施。pN が「exact-pin PASS は consultation を自動的に兼ねない・別 leg 要」と判定（`WMSO_PN_D11B_V13_PASS_DECLARED_OPEN_TRANSCRIPT_20260720.md` @ `7ce2a520c9`）ゆえの独立 leg。D1.1-A 先例（`WMSO_PN_FREEZE_CONSULTATION_TRANSCRIPT_20260719.md` @ `6af253dc14`）の 3 部形式に従う。
**性質:** OPS の custody/evidence consultation であって設計再検証ではない（設計軸 = pS 機構 + pN exact-pin、両 PASS）。⛔**freeze 自体は Rs 専権** — 本書は上程 input。

## ⭐ 結論: **GO 推奨**（custody/evidence lens で freeze-ready）

## 検証した pin（独立再計算・full-16 一致）

| 対象 | sha256(16) | commit | freshness |
|---|---|---|---|
| DESIGN v13（tensor_binding） | `5a1874d3be8b98b8` | `07250f4a02` | ✅最新（07-20 23:11 以降不変） |
| pS §33（設計軸 verify） | `f4a2f440bcb26071` | `37ffb8f653` | ✅最新（07-21 00:23） |

⇒ **freeze package は本 consultation 依頼（00:21）以降 動いていない**（byte 不変を実測）。

## (1) GO 根拠

- **3 軸 CLOSE を独立確認:**
  - **機構（設計軸）= pS §33 PASS** — 実読: pQ の原主張「契約層は駆動/保持を区別できない」を pS が**撤回検証**（frozen `00192d20ca00` 実測・`ControlMode = {DIFF_IK_EE_TARGET | SCRIPTED_SEQUENCE | WAIT}` で hold 単位 = `kind=WAIT ∧ control_mode=WAIT ∧ 資源 claim` として表現可 ⇒ **区別できる**）。
  - **pin（exact-pin）= pN v13 PASS**（transcript @ `7ce2a520c9`・実在確認）。
  - **authority = Rs ratify 21:44**（B1 委譲・逐語「はい」・DDR#27 CLOSE 記録）。B1-locator は D1.1-B の中核設計判断（D-1 採択）ゆえ本 ratify が authority 軸を成す。
- **declared-open を honest に宣言**（`§401`「『open=0』の無条件宣言はしない」= anti-under-statement 規律を明示）。
- **arity（枝数 B/A）は tensor_binding に非依存**（DESIGN 全文 grep = arity/ParallelRegion 0 hit）⇒ **arity SUSPENDED は D1.1-B freeze を block しない**（arity は composition/#2 の別 open・Rs 専権のまま）。

## (2) freeze 時に閉じる record-risk（= 封印される declared-open 4・pQ 依頼の独立判定）

⚠ freeze は 4 項を「**open として**」封印する（「解決済」としてではない）。各 risk 記述の過大/過小を独立判定:

| # | declared-open | risk 記述 | 判定 |
|---|---|---|---|
| 1 | **stats_key 一意性**（§10 `:64`） | length 不一致は fail-closed だが**同一 length 共有は検出 code 不在 = silent-pass** | ✅**正確**（neither over/under）。⭐旧「どちらの読みでも fail-closed」= over-claim は **v13 で訂正済**（commit `07250f4a02`「correct the stats_key risk overclaim」・pS 指摘）。現記述は silent-pass を正直に開示 |
| 2 | **§7 到達性負例** | impl leg（到達不能 error code の負例は実装時検証） | ✅正確（design-freeze blocker でなく impl-time coverage） |
| 3 | **§5 閾値系** | slice prereg + Rs（閾値は slice 設計判断 + Rs） | ✅正確 |
| 4 | **U-2 / U-5 / U-6** | D1.1-C prereg 必須入力（`§399`）= DDR #28/#29/#30 | ✅正確（producer artifact 阻止 / demo 移行 / topology ledger 束縛） |

⇒ **4 項とも過大でも過小でもない。** pQ が懸念した stats_key ① の over-claim は v13 で既に是正済で、現状は正直な silent-pass 開示。pS §33 が watch 軸に **under-statement（凍結語彙過小）** を追加したのも妥当（本 node は over・under 両方の申告誤りの履歴を持つ — §33 で pQ の under-statement 1 件を pS が捕捉）。

⚠ **封印される追加 record-risk（原則）:** 「bank ≠ verify」（DDR#27 §18 逐語「真偽を ratify できるのは Rs のみ」）は不変 — freeze は**設計書面の確定**であって真偽の証明ではない。

## (3) 次順序

**A. D1.1-B freeze（Rs 専権）** → **B. D1.1-C artifact_manifest**（U-2/U-5/U-6 を消費）→ **C. slice（2〜3 skill boundary-only vertical slice）**。impl / training / authority = CLOSED 継続。

## 非主張

- ⛔ 設計の再検証はしない（pS 機構 + pN exact-pin が設計軸・両 PASS）。本 leg = custody/evidence の freeze-readiness + risk 記述の accuracy。
- ⛔ freeze = Rs 専権。本 GO 推奨は上程 input であって freeze 実行ではない。
- ⛔ arity（Rs 専権・SUSPENDED）は本 freeze の対象外（tensor_binding 非依存）。

---
**consultation = 2026-07-21 10:5x JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
