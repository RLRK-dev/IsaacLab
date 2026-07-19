# WMSO D1.1-A 成果物 manifest（2026-07-19 20:40 JST 全面書換実測 — **Rs review v7 ⛔HOLD の fold 完了・pS 照合待ち**）

作成 = w2:pQ (RS-TECH-LEAD2)、node `T-WMSO`。全 sha256 = full 64-hex・**committed blob から実算出**（bank commit 付き — dirty tree 由来の pin なし）。本 manifest は RV7-R-3（旧 manifest = v2.9 世代 pin の残置）への全面書換。

## 現在地（1 行）
**Rs review v7（RV7 ⛔HOLD、v2.9.2 宛）の全項 fold = DESIGN v2.10 + EvidencePolicy v1.8 + JSON v1.8（bank `a87525cc15`）** → 残 gate = **pS 差分照合 → pN exact-pin 再検証（最終 SHA のみ渡す）→ Rs freeze 判定**（RV7 工程 12-14）。impl / training / authority = CLOSED 不変。

## 最終 pin（現行候補 — bank `a87525cc15`、worktree == committed blob 検証済み）
| artifact | 版 | sha256 |
|---|---|---|
| DESIGN | **v2.10** | `86a882219780dc43ad10dd38988c9933454a6892fb2f2721e83d843841e749c3` |
| EvidencePolicy markdown | **v1.8** | `9713cafbd2919c5d8a715412b125ae749e57f6cbf9ebdccc467d2699d83c8103` |
| JSON fixture `WMSO_EvidencePolicy_v1.8.json` | **v1.8**（policy_semver 1.8.0） | `00032f90916b56abe9ae54e626eb3f47e7d271bd06b48153d396a9bf2003c88c` |
| `evidence_policy_definition_hash` | H_WCJ(policy_definition)・17 member | `bdc508200889005142eaab5ac15c48cdfb8281df63bbb35537542f1f248891a8`（committed blob から埋込 command で再計算一致） |
| RV7 transcript | as-received（byte N/A・Rs fidelity PENDING） | `91923be57c206eaafa0b6cf938bbabc431cbefe223928f3dd1c3ecf5ea509732` |

⚠ **退役 pin（RV7 指示「最終 exact pin として使ってはいけません」）**: 旧 EP 系 `066eed1049f4f51a89dd86e9d50614a65adba070b2ff650424ea7cef05dec4ea`（definition hash v1.7 系）/ `ed10c77a4d9957368380195ee081368da3fdaa170b03ec275584e08d1c301faa`（JSON v1.7 file）— P0-2/3/4 の semantic 変更につき v1.8 系へ置換。

## 版系譜（design / EP — 全 sha は design v2.10 header の version 履歴が正）
- DESIGN: v2.9 `e64c192b62…`@`8caa19a7a4` → v2.9.1 `0da7932103…`@`ea30e7fdc3` → v2.9.2 `e83a29061400…`@`ba69702cb9`（pN evidence 軸 ✅PASS-CLOSE 17:43 → **Rs RV7 ⛔HOLD** — companion custody FAIL + P0-2..7/R-1..4）→ **v2.10 `86a8822197…`@`a87525cc15`（RV7 fold — 現行候補）**
- EvidencePolicy: v1.7 `586fec2a77…`@`8caa19a7a4` → v1.7.1 `27701698ed…`@`ba69702cb9`（pN R1 CLOSE — §3d 重複行統一）→ **v1.8 `9713cafbd2…`@`a87525cc15`（semantic bump — resolver 優先順位 / projection / CONFIG_HASH total map / evaluation wiring）**

## RV7 custody 事実確認（転記者注の要旨）
RV7 の review 環境 companion（EP `586fec2a…` = v1.7 / JSON `3fb7a452…` / manifest `a5d0aa0c…`）は**旧 zip 世代** — 20:10 JST 実測で現 `~/Downloads/`・repo とも v1.7.1/最終 JSON に更新済みだった（pQ の 19:49 design 単体納品時に companion pointer を添えなかった納品 gap）。**custody FAIL 判定自体は妥当**。RV7-P0-1 の semantic 部分（EP 重複行）は v1.7.1 で既修正（pN R1-R3 CLOSE が独立確認）、custody 部分は本 bundle で解消。**P0-2..P0-7 / R-1..R-4 は最終版 artifact 上にも実在 — pQ on-disk 検証の上、全て v2.10/v1.8 で fold**（fold-map = design §11 RV7 節）。

## 本 bundle（`~/Downloads/` — 本 manifest と同期）
| file | 内容 | sha256 |
|---|---|---|
| `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` | **DESIGN v2.10（現行候補）** | `86a882219780…`（上表） |
| `WMSO_D11A_DESIGN_v2.9.2_SUPERSEDED_20260719.md` | RV7 の review 対象だった v2.9.2 の保全 copy（diff 監査用） | `e83a29061400b42c18a6607c96295e0ede2984cda8b9b047f338512ccb0b7f96` |
| `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md` | **EvidencePolicy v1.8** | `9713cafbd2…`（上表） |
| `WMSO_EvidencePolicy_v1.8.json` | 機械可読 fixture（二層・17 member・golden vector 2 本掲載） | `00032f9091…`（上表） |
| `WMSO_RS_REVIEW_V7_HOLD_TRANSCRIPT_20260719.md` | RV7 as-received 転記 + custody 事実確認注 | `91923be57c…`（上表） |
| `WMSO_D11A_DESIGN_VERIFY_WMSODESIGN_20260719.md` | pS verify record §1-§15（v2.9.2 期まで） | `7a212b9374e3ae3f576031987b7483783a19a231041b6cbb3f4e6be060bf81dc` |
| `WMSO_PN_DESIGN_VERIFY_HOLD_C1C3_TRANSCRIPT_20260719.md` | pN HOLD C1-C3 transcript | `d8b5f83e0af85cd069feec73c011ef3949d1a258ec61348565e0f2149fe6e4c2` |
| `WMSO_PN_DESIGN_VERIFY_R_AND_PASSCLOSE_TRANSCRIPT_20260719.md` | pN R1-R3 HOLD + ✅PASS-CLOSE（v2.9.2 宛）transcript | `2847e2aa9d30a9b57093232425c8fdbef2aa09a87d0291b489f79e471f911139` |
| `WMSO_RS_REVIEW_V6_COPY_20260719.md` | Rs review v6 byte-identical copy | `3f64cbca44269bc8255fd2c0dcf4d96712248de4017d4b1943c0855daef2cead` |
| `WMSO_RS_REVIEW4_FIDELITY_CONFIRM_20260719.md` | review-4 fidelity 確認 record | `f5737799522c7e679753299fe7ece1d9ae51caf6df723ee7f48cf54e1a7c15c8` |

（Rs 発行 review v3/v4/v5 原本 = `~/Downloads/PLAN_STATUS_review_v{3,4,5}_2026-07-19.md` 既在。repo byte-identical copy = `20da075f9566…` / `338bdaf75a99…` / `44792e860e82…`。pN B1-B7 transcript = repo `6d26efde4739…`@`86d127b5c0`。）

## 残 gate（RV7 工程 12-14 — 順不同にしない）
1. **pS 差分照合**（v2.9.2→v2.10 差分 + EP v1.7.1→v1.8 — 依頼済み）
2. **pN exact-pin 再検証**（pS PASS 後に**最終 SHA のみ**渡す）
3. **Rs freeze 判定**（pN PASS 後に上程）

## 未 push
`a87525cc15`（fold）+ 本 manifest commit。**push は Rs 一言で実行**（`1fb038bc39` までは push 済み・remote 一致確認 19:46）。
