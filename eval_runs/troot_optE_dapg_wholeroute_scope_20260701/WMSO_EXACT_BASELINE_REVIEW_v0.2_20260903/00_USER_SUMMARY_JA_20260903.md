# WMSO v0.2 レビュー package — 利用者向け要約（日本語）

- 記録 = 2026-09-04 20:48 UTC（`date -u` 実測）。本 file は package の読み方の案内であり、規範文書ではない。
- 状態: **REVIEW CANDIDATE v0.2.3・未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない**。impl / training / closed-loop authority / production / freeze / slice = CLOSED のまま。

## 1. 何が入っているか

| file | 役割 |
|---|---|
| `01_BASELINE_CUSTODY_VERIFICATION_20260903.md` + `verify_exact_baseline_pins.sh` + `09_BASELINE_PIN_20260903.json` | 凍結 4 file（contracts_v2 DESIGN v2.11.2・EP v1.9 md / JSON・tensor_binding DESIGN v13）の exact pin と再測手順（11/11 PASS） |
| `02_…csv` / `03_…csv` | 旧 v0.1 の項目が凍結物と重なるか（home matrix）／ 変更 class が hash 面を動かすか（identity impact） |
| `04_…md` | EP v1.9 は不変（definition hash 不変）という影響評価 |
| `05_WMSO_RUNTIME_SPEC_…md` | **runtime spec v0.2.3**（boundary-only・TERMINAL boundary・checkpoint 切替なし。AuthorityManager / CommandGateway / CAS / lease / SafeHold / audit） |
| `06_WMSO_INDUSTRIAL_PROFILE_…md` | **industrial deployment profile v0.2.3**（cell 固有条件を content-addressed にし、凍結意味論を狭める方向にしか使えない） |
| `07_…md` | 後継静的契約は今は作らない（`contracts_v3` は静的意味論の認証時のみ）という判断 |
| `08_…md` | 3 軸独立レビュー計画（contract / runtime / deployment） |
| `10_…md` + `review_records/PC_*` | 陽性対照（欠陥を注入した複製で計器を検証。7/8 検出・盲点は checker O3 で機械化） |
| `11_THREE_AXIS_REVIEW_RECORD_20260903.md` + `review_records/AXIS_*` / `VERIFY_*` | **3 軸レビューの実施記録**（reviewer 5 体・verifier 5 体・全 80 finding の verdict と処置） |
| `review_records/fold/*` | v0.2.1 → v0.2.2 → v0.2.3 の fold を再現する script と verifier verdict の JSON |
| `check_review_candidate.py` / `SHA256SUMS.txt` | 機械検査（FAIL = 0 が要件）／ content sha（版 label でなく sha で引く） |

## 2. レビューの結果（事実・数値は 11_ §2 から）

- finding 総数 80（A 12 / A2 12 / B 21 / B2 17 / C 18）。independent verifier（3 lens: text / logic / impact）が 80 件全てを判定。
- confirmed 79・refuted 1（A2-09 = 反循環文の文言のみ・NOT_A_DEFECT）。
- v0.2.2 の fold 状態（A/A2/B/B2 の 61 件）: RESOLVED 49・PARTIAL 12・NOT_RESOLVED 0。PARTIAL 12 件の残差は v0.2.3 で処置。
- 軸 C（deployment）は v0.2.2 を対象に 18 件（reviewer: HIGH 4 / MEDIUM 6 / LOW 8 → verifier: HIGH 3 / MEDIUM 8 / LOW 7）。全件 v0.2.3 で fold。
- 主な設計変更（v0.2.2 → v0.2.3）: timeout の相対順序検査 `P_TIMEOUT_ORDER`／ clearance role の被覆 `P_CLEARANCE_ROLE_MISSING`／ evidence の失効・subject 単位執行 `P_EVIDENCE_EXPIRED`／ predicate・evaluator の content hash／ lease の時間上限 `lease_max_duration_s`／ health check に identity 確認／ 閉じた enum（calibration kind・zone kind）／ envelope の空虚化防止。
- 機械検査: 全 doc / csv で FAIL = 0（11_ §6 に実測出力）。

## 3. 何を主張していないか（読み手が誤解しやすい点）

- reviewer / verifier は AI（別 context の subagent）。**human two-key（pS / pY / Rs）ではない**。08 §6 の位置づけ = 予備レビュー。
- v0.2.3 本文そのものに対する再レビュー・再 verify は未実施（次 round）。「open = 0」は宣言しない（05 §12・06 §10 に open が残る）。
- 前 package（v0.1）は本 sandbox に無く、handoff 決定から再構成した（01 §で honest に記録）。judge panel（3 draft × 2 judge）は session 上限で未実施。
- 凍結 4 file には触れていない（pin 再測 11/11 PASS）。schema delta 0。

## 4. 次に人が判断すること（提案・Rs 専権）

1. v0.2.3 を two-key review（pS / pY）に回すか、先に v0.2.3 対象の AI 再 round（reviewer × verifier）を 1 回挟むか。
2. 06 OPP-11（timeout の絶対上限）・OPP-13（profile registry と受理権限）・05 OP-19（lease 中の周期再評価）は設計判断が要る open。
3. `contracts_v3` を起票しない判断（07）の追認。
